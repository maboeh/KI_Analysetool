"""Spaltenrollen-Erkennung, Fehlwert-Handling und erklärbare Diagrammvorschläge.

Ergänzt `chart_generator.ChartGenerator` um eine rein regelbasierte Analyse
einer `DataTable`: Jede Spalte bekommt eine Rolle (numeric, date, categorical,
text), Fehlwerte werden gezählt und Diagrammvorschläge werden mit einer
nachvollziehbaren Begründung versehen.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from data_models import DataTable


MISSING_VALUES = {"", "-", "--", "n/a", "na", "n.a.", "null", "none", "?"}

_DATE_FORMATS = (
    "%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d",
    "%d. %B %Y", "%B %Y", "%Y",
)

_NUMBER_PATTERN = re.compile(r"^-?\d{1,3}([.\s]\d{3})*(,\d+)?$|^-?\d+(\.\d+)?$|^-?\d+$")


@dataclass(frozen=True)
class ColumnProfile:
    """Erkannte Rolle und Qualität einer Tabellenspalte."""

    index: int
    header: str
    role: str                 # numeric | date | categorical | text
    total: int
    missing: int
    unique_count: int

    @property
    def missing_share(self) -> float:
        return self.missing / self.total if self.total else 0.0


@dataclass(frozen=True)
class SmartChartSuggestion:
    """Erklärbarer Diagrammvorschlag für eine Tabelle."""

    chart_type: str           # bar | line | pie | scatter | histogram
    x_column: Optional[str]
    y_columns: List[str] = field(default_factory=list)
    reason: str = ""
    missing_value_hint: str = ""
    confidence: float = 0.5


def is_missing(value) -> bool:
    return value is None or str(value).strip().lower() in MISSING_VALUES


def _parse_number(value: str) -> Optional[float]:
    """Parst Zahlen inkl. deutscher Formatierung (1.234,56)."""
    text = str(value).strip()
    if not _NUMBER_PATTERN.match(text):
        return None
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def _parse_date(value: str) -> Optional[datetime]:
    text = str(value).strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def analyze_columns(table: DataTable) -> List[ColumnProfile]:
    """Bestimmt Rolle und Fehlwertanteil jeder Spalte einer Tabelle."""
    profiles: List[ColumnProfile] = []
    for index, header in enumerate(table.headers):
        column = [row[index] for row in table.rows if index < len(row)]
        total = len(column)
        missing = sum(1 for v in column if is_missing(v))
        filled = [v for v in column if not is_missing(v)]
        unique_count = len({str(v).strip() for v in filled})

        if filled and sum(1 for v in filled if _parse_number(v) is not None) / len(filled) >= 0.8:
            role = "numeric"
        elif filled and sum(1 for v in filled if _parse_date(v) is not None) / len(filled) >= 0.8:
            role = "date"
        elif filled and unique_count <= max(10, len(filled) // 2):
            role = "categorical"
        else:
            role = "text"

        profiles.append(ColumnProfile(
            index=index, header=str(header), role=role,
            total=total, missing=missing, unique_count=unique_count,
        ))
    return profiles


def clean_column(values: List, strategy: str = "drop_missing") -> List[Optional[float]]:
    """Bereinigt eine Spalte zu Zahlenwerten.

    Strategien:
        drop_missing: fehlende/unparsbare Werte werden None
        zero:         fehlende/unparsbare Werte werden 0.0
        mean:         fehlende/unparsbare Werte werden durch den Mittelwert ersetzt
    """
    parsed = [None if is_missing(v) else _parse_number(str(v)) for v in values]
    if strategy == "drop_missing":
        return parsed
    if strategy == "zero":
        return [0.0 if v is None else v for v in parsed]
    if strategy == "mean":
        valid = [v for v in parsed if v is not None]
        mean = sum(valid) / len(valid) if valid else 0.0
        return [mean if v is None else v for v in parsed]
    raise ValueError(f"Unbekannte Strategie: {strategy}")


def _missing_hint(profiles: List[ColumnProfile], columns: List[str]) -> str:
    affected = [p for p in profiles if p.header in columns and p.missing > 0]
    if not affected:
        return ""
    details = ", ".join(f"'{p.header}' ({p.missing}/{p.total} fehlend)" for p in affected)
    return f"Fehlwerte in {details} – vor Visualisierung bereinigen."


def suggest_charts(table: DataTable) -> List[SmartChartSuggestion]:
    """Erzeugt begründete Diagrammvorschläge aus den Spaltenrollen."""
    profiles = analyze_columns(table)
    if len(table.rows) < 2 or not profiles:
        return []

    numeric = [p for p in profiles if p.role == "numeric"]
    dates = [p for p in profiles if p.role == "date"]
    categorical = [p for p in profiles if p.role == "categorical"]
    suggestions: List[SmartChartSuggestion] = []

    if dates and numeric:
        y_cols = [p.header for p in numeric[:3]]
        suggestions.append(SmartChartSuggestion(
            chart_type="line", x_column=dates[0].header, y_columns=y_cols,
            reason=(f"Zeitverlauf: Datums-Spalte '{dates[0].header}' auf der X-Achse "
                    f"mit {len(y_cols)} numerischen Spalte(n)."),
            missing_value_hint=_missing_hint(profiles, [dates[0].header, *y_cols]),
            confidence=0.9,
        ))

    if categorical and numeric:
        y_cols = [p.header for p in numeric[:2]]
        suggestions.append(SmartChartSuggestion(
            chart_type="bar", x_column=categorical[0].header, y_columns=y_cols,
            reason=(f"Vergleich: Kategorie-Spalte '{categorical[0].header}' mit "
                    f"{categorical[0].unique_count} Gruppen gegenüber numerischen Werten."),
            missing_value_hint=_missing_hint(profiles, [categorical[0].header, *y_cols]),
            confidence=0.85,
        ))
        if categorical[0].unique_count <= 8:
            suggestions.append(SmartChartSuggestion(
                chart_type="pie", x_column=categorical[0].header,
                y_columns=[numeric[0].header],
                reason=(f"Anteile: nur {categorical[0].unique_count} Kategorien in "
                        f"'{categorical[0].header}' – gut für ein Kreisdiagramm."),
                missing_value_hint=_missing_hint(
                    profiles, [categorical[0].header, numeric[0].header]),
                confidence=0.7,
            ))

    if len(numeric) >= 2:
        suggestions.append(SmartChartSuggestion(
            chart_type="scatter",
            x_column=numeric[0].header, y_columns=[numeric[1].header],
            reason=(f"Zusammenhang: zwei numerische Spalten '{numeric[0].header}' "
                    f"und '{numeric[1].header}'. "),
            missing_value_hint=_missing_hint(
                profiles, [numeric[0].header, numeric[1].header]),
            confidence=0.6,
        ))
    elif len(numeric) == 1 and not categorical and not dates:
        suggestions.append(SmartChartSuggestion(
            chart_type="histogram", x_column=numeric[0].header, y_columns=[],
            reason=f"Verteilung: einzige numerische Spalte '{numeric[0].header}'.",
            missing_value_hint=_missing_hint(profiles, [numeric[0].header]),
            confidence=0.55,
        ))

    suggestions.sort(key=lambda s: s.confidence, reverse=True)
    return suggestions
