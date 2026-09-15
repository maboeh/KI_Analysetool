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
    "primary+k": "Befehlspalette öffnen",
    "primary+shift+p": "Prompt-Playground öffnen",
    "primary+b": "Batch-Verarbeitung öffnen",
    "primary+comma": "Einstellungen öffnen",
}
IMPLEMENTED_FEATURES = frozenset({
    "analysis_history",
    "auto_save",
    "backup_restore_full",
    "backup_restore_hardened",
    "batch_queue",
    "batch_result_export",
    "chart_suggestions",
    "command_palette",
    "cost_estimate",
    "drag_drop",
    "empty_states",
    "evaluation_suite",
    "evidence_validation",
    "excel_export",
    "favorites",
    "follow_up_actions",
    "keyboard_shortcuts",
    "learning_path",
    "local_provider",
    "ocr",
    "packaged_desktop_build",
    "update_check",
    "pdf_report",
    "privacy_scan",
    "projects",
    "prompt_library",
    "prompt_playground",
    "recipes",
    "result_comparison",
    "result_diff",
    "result_data_editing",
    "result_editing",
    "result_search",
    "result_versions",
    "schema_migrations",
    "session_budget",
    "tags",
    "token_cost_tracking",
    "transfer_confirmation",
    "visualization",
})
MODEL_IDS = tuple(AVAILABLE_MODELS.keys())
