from dataclasses import dataclass
from typing import Dict, Tuple

from analysis import AVAILABLE_MODELS
from data_models import ChartType


@dataclass(frozen=True)
class InputCapability:
    id: str
    label: str
    extensions: Tuple[str, ...] = ()
    supports_drag_drop: bool = False


INPUT_CAPABILITIES = (
    InputCapability("text", "Direkter Text"),
    InputCapability("website", "Webseite"),
    InputCapability("youtube", "YouTube"),
    InputCapability("pdf", "PDF", (".pdf",), True),
    InputCapability("excel", "Excel", (".xlsx", ".xls"), True),
    InputCapability("image", "Bild/PDF mit OCR", (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".pdf"), True),
    InputCapability("csv", "CSV/Text", (".csv", ".tsv", ".txt"), True),
    InputCapability("multi", "Mehrere Dateien", (".xlsx", ".xls", ".csv", ".tsv", ".txt", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".pdf"), True),
)

RESULT_EXPORT_FORMATS = ("json", "txt", "csv", "xlsx", "pdf")
CHART_EXPORT_FORMATS = ("png", "pdf", "svg")
CHART_TYPES = tuple(chart_type.value for chart_type in ChartType)
SHORTCUTS: Dict[str, str] = {
    "primary+return": "Analyse starten",
    "primary+s": "Aktuelles Ergebnis speichern",
    "primary+e": "Aktuelles Ergebnis als PDF exportieren",
    "primary+f": "Favoriten anzeigen",
}
IMPLEMENTED_FEATURES = frozenset({
    "analysis_history",
    "auto_save",
    "backup_restore_full",
    "batch_result_export",
    "drag_drop",
    "excel_export",
    "favorites",
    "follow_up_actions",
    "learning_path",
    "ocr",
    "pdf_report",
    "prompt_library",
    "result_comparison",
    "result_search",
    "tags",
    "token_cost_tracking",
    "visualization",
})
MODEL_IDS = tuple(AVAILABLE_MODELS.keys())
