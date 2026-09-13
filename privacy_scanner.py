"""Lokaler Datenschutz-Scanner für ausgehende Inhalte.

Erkennt personenbezogene Daten und mögliche Geheimnisse (API-Keys,
Passwörter, Tokens) rein lokal per Heuristik, bevor Inhalte an einen
externen KI-Anbieter übertragen werden. Keine Netzwerkzugriffe, keine
Telemetrie – alle Prüfungen laufen im Prozess.
"""

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class PrivacyFinding:
    """Ein einzelner erkannter Datenschutz-Fund."""

    kind: str
    label: str
    start: int
    end: int
    masked_preview: str


@dataclass(frozen=True)
class PrivacyReport:
    """Ergebnis eines Scans."""

    findings: List[PrivacyFinding]

    @property
    def has_findings(self) -> bool:
        return bool(self.findings)

    def count_by_kind(self) -> dict:
        counts = {}
        for finding in self.findings:
            counts[finding.kind] = counts.get(finding.kind, 0) + 1
        return counts


def _mask_match(value: str) -> str:
    """Maskiert einen Fund für die Anzeige (max. Anfang und Ende sichtbar)."""
    value = value.strip()
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:3]}{'*' * (len(value) - 6)}{value[-3:]}"


def _luhn_valid(digits: str) -> bool:
    """Luhn-Prüfsumme zur Reduktion von Kreditkarten-Fehlmeldungen."""
    total = 0
    for index, char in enumerate(reversed(digits)):
        digit = int(char)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _iban_valid(value: str) -> bool:
    """ISO-13616-Mod-97-Prüfung zur Reduktion von IBAN-Fehlmeldungen."""
    compact = re.sub(r"\s+", "", value)
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", compact):
        return False
    rearranged = compact[4:] + compact[:4]
    numeric = ""
    for char in rearranged:
        numeric += str(ord(char) - 55) if char.isalpha() else char
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False


# (kind, label, pattern, validator)
_PATTERNS = (
    (
        "api_key",
        "API-Schlüssel / Token",
        re.compile(
            r"\b(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|"
            r"xox[baprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|"
            r"AIza[0-9A-Za-z_-]{20,})\b"
        ),
        None,
    ),
    (
        "secret_assignment",
        "Mögliches Passwort/Secret",
        re.compile(
            r"(?i)\b(?:password|passwd|passwort|pwd|api[_-]?key|secret|"
            r"token|access[_-]?key|client[_-]?secret)\b\s*[:=]\s*"
            r"['\"]?[^\s'\"]{8,}"
        ),
        None,
    ),
    (
        "email",
        "E-Mail-Adresse",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        None,
    ),
    (
        "iban",
        "IBAN / Bankverbindung",
        re.compile(r"\b[A-Z]{2}\d{2}(?: ?\d{4}){3,6}(?: ?\d{1,4})?\b"),
        _iban_valid,
    ),
    (
        "credit_card",
        "Kreditkartennummer",
        re.compile(r"\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6(?:011|5\d{2}))"
                   r"(?:[ -]?\d{4}){3}(?:[ -]?\d{1,3})?\b"),
        lambda value: _luhn_valid(re.sub(r"[ -]", "", value)),
    ),
    (
        "phone",
        "Telefonnummer",
        re.compile(
            r"(?:\+\d{1,3}|\(0\d{1,5}\)|\b0\d{2,5})[ /-]\d[\d /-]{4,}\d"
        ),
        None,
    ),
)


def scan_text(text: str) -> PrivacyReport:
    """Scannt Text lokal auf personenbezogene Daten und Secrets.

    Returns:
        PrivacyReport mit deduplizierten, nicht überlappenden Funden.
    """
    if not isinstance(text, str) or not text.strip():
        return PrivacyReport(findings=[])

    findings: List[PrivacyFinding] = []
    occupied: List[tuple] = []

    for kind, label, pattern, validator in _PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span()
            value = match.group(0)

            # Überlappungen mit höher priorisierten Funden überspringen.
            if any(start < occ_end and end > occ_start for occ_start, occ_end in occupied):
                continue
            if validator is not None and not validator(value):
                continue

            occupied.append((start, end))
            findings.append(PrivacyFinding(
                kind=kind,
                label=label,
                start=start,
                end=end,
                masked_preview=_mask_match(value),
            ))

    findings.sort(key=lambda finding: finding.start)
    return PrivacyReport(findings=findings)


def redact_text(text: str, report: Optional[PrivacyReport] = None) -> str:
    """Ersetzt alle erkannten Funde durch Platzhalter.

    Args:
        text: Der zu schwärzende Text.
        report: Optionaler bestehender Report; wird sonst neu erstellt.

    Returns:
        Text mit geschwärzten Fundstellen.
    """
    if report is None:
        report = scan_text(text)

    redacted = text
    for finding in sorted(report.findings, key=lambda f: f.start, reverse=True):
        placeholder = f"[{finding.label} entfernt]"
        redacted = redacted[:finding.start] + placeholder + redacted[finding.end:]
    return redacted
