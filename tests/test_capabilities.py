import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import AVAILABLE_MODELS
from capabilities import (
    CHART_EXPORT_FORMATS,
    CHART_TYPES,
    IMPLEMENTED_FEATURES,
    INPUT_CAPABILITIES,
    MODEL_IDS,
)
from csv_handler import CSVHandler
from data_models import ChartType
from excel_handler import ExcelHandler
from image_handler import ImageHandler


class TestCapabilities(unittest.TestCase):
    def test_models_and_chart_types_match_runtime(self):
        self.assertEqual(MODEL_IDS, tuple(AVAILABLE_MODELS.keys()))
        self.assertEqual(CHART_TYPES, tuple(chart_type.value for chart_type in ChartType))

    def test_input_extensions_match_handlers(self):
        by_id = {capability.id: capability for capability in INPUT_CAPABILITIES}
        self.assertEqual(set(by_id["excel"].extensions), set(ExcelHandler.SUPPORTED_EXTENSIONS))
        self.assertEqual(set(by_id["image"].extensions), set(ImageHandler.SUPPORTED_EXTENSIONS))
        self.assertEqual(set(by_id["csv"].extensions), set(CSVHandler.SUPPORTED_EXTENSIONS))

    def test_documented_core_capabilities_are_registered(self):
        self.assertIn("drag_drop", IMPLEMENTED_FEATURES)
        self.assertIn("backup_restore_full", IMPLEMENTED_FEATURES)
        self.assertEqual(CHART_EXPORT_FORMATS, ("png", "pdf", "svg"))

    def test_documentation_marks_unimplemented_features(self):
        root = Path(__file__).resolve().parent.parent
        combined = "\n".join(
            (root / filename).read_text(encoding="utf-8")
            for filename in ("HELP.md", "USER_GUIDE.md")
        )
        self.assertIn("Automatische tägliche Backups", combined)
        self.assertIn("HTML-Diagrammexport", combined)
        self.assertIn("derzeit nicht", combined)


if __name__ == "__main__":
    unittest.main()
