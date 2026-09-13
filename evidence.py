"""Quellenbelege: Zitate und Referenzen in Analyseergebnissen prüfen.

Extrahiert aus einem Ergebnistext Zitate und Referenzen (Seiten-, Abschnitts-,
Zeilen- und Zeitangaben) und validiert sie gegen den Original-Quelltext.

Statuslogik (bewusst konservativ, nichts wird "verifiziert", was nicht
wörtlich oder strukturell belegt ist):
- verified:      wörtliches Zitat im Quelltext gefunden (Whitespace-normalisiert;
                 bei gepaginaten Quellen wird die Fundseite genannt)
- unverified:    prüfbar, aber nicht gefunden bzw. Referenz zeigt auf etwas,
                 das in der Quelle nicht existiert (z. B. Seite 99 bei einem
                 3-seitigen Dokument)
- plausible:     Referenz existiert strukturell (Seite vorhanden, Zeitstempel
                 innerhalb der Videodauer), der Inhalt ist aber nicht geprüft
- not_checkable: ohne Quelltext/-struktur nicht prüfbar
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# Status-Konstanten
STATUS_VERIFIED = "verified"
STATUS_UNVERIFIED = "unverified"
STATUS_PLAUSIBLE = "plausible"
STATUS_NOT_CHECKABLE = "not_checkable"


@dataclass(frozen=True)
class SourceDocument:
    """Quelltext mit optionaler Struktur für tiefere Belegprüfung.

    pages:    Text pro Seite (z. B. per OCR extrahierte PDF-Seiten)
    duration: Gesamtdauer in Sekunden (z. B. bei YouTube-Transkripten)
    """

    text: str
    pages: List[str] = field(default_factory=list)
    duration: Optional[float] = None


@dataclass(frozen=True)
class Citation:
    """Eine erkannte Referenz oder ein Zitat im Ergebnistext."""

    kind: str           # quote | page | section | line | timestamp
    text: str           # erkannter Text (z. B. das Zitat oder "Seite 3")
    start: int
    end: int
    status: str = STATUS_NOT_CHECKABLE
    source_excerpt: str = ""


@dataclass(frozen=True)
class EvidenceReport:
    """Validierungsergebnis für ein Analyseergebnis."""

    citations: List[Citation] = field(default_factory=list)
    source_available: bool = True

    @property
    def verified_count(self) -> int:
        return sum(1 for c in self.citations if c.status == STATUS_VERIFIED)

    @property
    def unverified_count(self) -> int:
        return sum(1 for c in self.citations if c.status == STATUS_UNVERIFIED)

    @property
    def plausible_count(self) -> int:
        return sum(1 for c in self.citations if c.status == STATUS_PLAUSIBLE)

    @property
    def not_checkable_count(self) -> int:
        return sum(1 for c in self.citations if c.status == STATUS_NOT_CHECKABLE)


# Zitate in verschiedenen Anführungszeichen (mind. 20 Zeichen, um Labels zu filtern)
_QUOTE_PATTERN = re.compile(
    r"[„\"]([^„\"“”]{20,500})[“\"]|'([^']{20,500})'"
)
_PAGE_PATTERN = re.compile(r"\b(?:Seite|S\.|Page|p\.)\s*(\d{1,4})\b")
_SECTION_PATTERN = re.compile(
    r"\b(?:Abschnitt|Section|Kapitel|Chapter)\s*([A-Za-z0-9][\w.\-]{0,20})")
_LINE_PATTERN = re.compile(r"\b(?:Zeile|Line)\s*(\d{1,6})\b")
_TIMESTAMP_PATTERN = re.compile(r"\b(\d{1,2}:\d{2}(?::\d{2})?)\b")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def _timestamp_to_seconds(value: str) -> float:
    parts = [int(p) for p in value.split(":")]
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + part
    return float(seconds)


def extract_citations(result_text: str) -> List[Citation]:
    """Extrahiert Zitate und Referenzen aus einem Ergebnistext."""
    if not isinstance(result_text, str) or not result_text.strip():
        return []

    citations: List[Citation] = []
    occupied: List[tuple] = []

    def _add(kind, text, start, end):
        if any(start < oe and end > os_ for os_, oe in occupied):
            return
        occupied.append((start, end))
        citations.append(Citation(kind=kind, text=text, start=start, end=end))

    for match in _QUOTE_PATTERN.finditer(result_text):
        quote = match.group(1) if match.group(1) is not None else match.group(2)
        _add("quote", quote.strip(), match.start(), match.end())
    for match in _PAGE_PATTERN.finditer(result_text):
        _add("page", match.group(0), match.start(), match.end())
    for match in _SECTION_PATTERN.finditer(result_text):
        _add("section", match.group(0), match.start(), match.end())
    for match in _LINE_PATTERN.finditer(result_text):
        _add("line", match.group(0), match.start(), match.end())
    for match in _TIMESTAMP_PATTERN.finditer(result_text):
        _add("timestamp", match.group(0), match.start(), match.end())

    citations.sort(key=lambda c: c.start)
    return citations


def _find_excerpt(source: str, quote: str, window: int = 160) -> Optional[str]:
    """Findet das Zitat whitespace-normalisiert und liefert einen Kontextauszug."""
    normalized_source = _normalize(source)
    normalized_quote = _normalize(quote)
    index = normalized_source.find(normalized_quote)
    if index < 0:
        return None
    start = max(0, index - window // 2)
    end = min(len(normalized_source), index + len(normalized_quote) + window // 2)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(normalized_source) else ""
    return f"{prefix}{normalized_source[start:end]}{suffix}"


def _find_quote_in_pages(pages: List[str], quote: str) -> Optional[int]:
    """Liefert die 1-basierte Seitenzahl, auf der das Zitat steht (oder None)."""
    for index, page in enumerate(pages):
        if _normalize(quote) in _normalize(page):
            return index + 1
    return None


def validate_evidence(result_text: str,
                      source) -> EvidenceReport:
    """Prüft alle erkannten Zitate/Referenzen gegen die Quelle.

    Args:
        result_text: Das Analyseergebnis.
        source: Quelltext (str), SourceDocument oder None, wenn die Quelle
                nicht verfügbar ist.
    """
    if isinstance(source, SourceDocument):
        source_text = source.text
        pages = source.pages
        duration = source.duration
    else:
        source_text = source or ""
        pages = []
        duration = None

    citations = extract_citations(result_text)
    if not citations:
        return EvidenceReport(citations=[], source_available=bool(source_text))

    checked = []
    for citation in citations:
        if citation.kind == "quote":
            if not source_text:
                checked.append(Citation(**{**citation.__dict__,
                                           "status": STATUS_NOT_CHECKABLE}))
                continue
            if pages:
                page_no = _find_quote_in_pages(pages, citation.text)
                if page_no is not None:
                    excerpt = _find_excerpt(pages[page_no - 1], citation.text) or ""
                    checked.append(Citation(
                        **{**citation.__dict__,
                           "status": STATUS_VERIFIED,
                           "source_excerpt": f"Seite {page_no}: {excerpt}"}))
                    continue
            excerpt = _find_excerpt(source_text, citation.text)
            status = STATUS_VERIFIED if excerpt is not None else STATUS_UNVERIFIED
            checked.append(Citation(
                **{**citation.__dict__, "status": status,
                   "source_excerpt": excerpt or ""}))
            continue

        if citation.kind == "page" and pages:
            match = re.search(r"\d+", citation.text)
            page_no = int(match.group(0)) if match else 0
            if 1 <= page_no <= len(pages):
                checked.append(Citation(
                    **{**citation.__dict__, "status": STATUS_PLAUSIBLE,
                       "source_excerpt":
                           f"Seite {page_no} existiert (Dokument: {len(pages)} Seiten)."}))
            else:
                checked.append(Citation(
                    **{**citation.__dict__, "status": STATUS_UNVERIFIED,
                       "source_excerpt":
                           f"Seite {page_no} existiert nicht – das Dokument hat "
                           f"nur {len(pages)} Seite(n). Möglicher erfundener Beleg."}))
            continue

        if citation.kind == "timestamp" and duration:
            seconds = _timestamp_to_seconds(citation.text)
            if seconds <= duration:
                checked.append(Citation(
                    **{**citation.__dict__, "status": STATUS_PLAUSIBLE,
                       "source_excerpt":
                           f"Zeitpunkt {citation.text} liegt im Video "
                           f"(Dauer ca. {int(duration // 60)}:{int(duration % 60):02d})."}))
            else:
                checked.append(Citation(
                    **{**citation.__dict__, "status": STATUS_UNVERIFIED,
                       "source_excerpt":
                           f"Zeitpunkt {citation.text} liegt hinter dem Videoende "
                           f"({int(duration // 60)}:{int(duration % 60):02d}). "
                           "Möglicher erfundener Beleg."}))
            continue

        # Abschnitts-/Zeilenangaben sowie nicht prüfbare Seiten/Zeiten.
        checked.append(Citation(**{**citation.__dict__,
                                   "status": STATUS_NOT_CHECKABLE}))

    return EvidenceReport(citations=checked, source_available=bool(source_text))
