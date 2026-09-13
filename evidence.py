"""Quellenbelege: Zitate und Referenzen in Analyseergebnissen prüfen.

Extrahiert aus einem Ergebnistext Zitate und Referenzen (Seiten-, Abschnitts-,
Zeilen- und Zeitangaben) und validiert sie gegen den Original-Quelltext.

Wichtig: Eine Referenz wird nur dann als „verified" markiert, wenn sie
tatsächlich überprüfbar ist – also bei wörtlichen Zitaten, die im Quelltext
(Whitespace-normalisiert) vorkommen. Seiten-/Abschnitts-/Zeitangaben ohne
überprüfbare Struktur werden als „not_checkable", nie als verifiziert,
markiert. Nicht gefundene Zitate sind „unverified".
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# Status-Konstanten
STATUS_VERIFIED = "verified"          # wörtlich im Quelltext gefunden
STATUS_UNVERIFIED = "unverified"      # prüfbar, aber nicht gefunden
STATUS_NOT_CHECKABLE = "not_checkable"  # ohne Quellstruktur nicht prüfbar


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


def validate_evidence(result_text: str, source_text: Optional[str]) -> EvidenceReport:
    """Prüft alle erkannten Zitate/Referenzen gegen den Quelltext.

    Args:
        result_text: Das Analyseergebnis.
        source_text: Originalinhalt; None wenn die Quelle nicht verfügbar ist.
    """
    citations = extract_citations(result_text)
    if not citations:
        return EvidenceReport(citations=[], source_available=bool(source_text))

    checked = []
    for citation in citations:
        if citation.kind != "quote":
            # Seiten-/Abschnitts-/Zeitangaben sind ohne Quellstruktur nicht prüfbar.
            checked.append(Citation(**{**citation.__dict__,
                                       "status": STATUS_NOT_CHECKABLE}))
            continue
        if not source_text:
            checked.append(Citation(**{**citation.__dict__,
                                       "status": STATUS_NOT_CHECKABLE}))
            continue
        excerpt = _find_excerpt(source_text, citation.text)
        status = STATUS_VERIFIED if excerpt is not None else STATUS_UNVERIFIED
        checked.append(Citation(
            kind=citation.kind, text=citation.text,
            start=citation.start, end=citation.end,
            status=status, source_excerpt=excerpt or "",
        ))

    return EvidenceReport(citations=checked, source_available=bool(source_text))
