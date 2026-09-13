import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_models import ProcessedResult, ResultMetadata, SourceInfo
from results_manager import ResultsManager


def _make_result(rid: str, content: str = "Original") -> ProcessedResult:
    return ProcessedResult(
        id=rid,
        content=content,
        source_info=SourceInfo(type="text"),
        metadata=ResultMetadata(analysis_type="text"),
    )


class TestResultVersions(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.manager = ResultsManager(str(self.tmp / "results.db"),
                                      str(self.tmp / "results"))
        self.manager.save_result(_make_result("r1"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_save_and_list_versions(self):
        v1 = self.manager.save_version("r1", "Version A", note="erste")
        v2 = self.manager.save_version("r1", "Version B")
        versions = self.manager.list_versions("r1")
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0]["version_no"], 2)
        self.assertEqual(versions[1]["note"], "erste")
        self.assertEqual(self.manager.get_version_content(v1), "Version A")
        self.assertEqual(self.manager.get_version_content(v2), "Version B")

    def test_save_version_unknown_result(self):
        self.assertIsNone(self.manager.save_version("unknown", "x"))

    def test_update_content_creates_prior_version(self):
        self.assertTrue(self.manager.update_result_content("r1", "Bearbeitet"))
        result = self.manager.load_result("r1")
        self.assertEqual(result.content, "Bearbeitet")
        versions = self.manager.list_versions("r1")
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0]["note"], "Vor Bearbeitung")

    def test_update_without_change_is_noop(self):
        self.manager.update_result_content("r1", "Original")
        self.assertEqual(self.manager.list_versions("r1"), [])

    def test_rollback_restores_content_and_keeps_current(self):
        self.manager.update_result_content("r1", "Version 2")
        versions = self.manager.list_versions("r1")
        old_version = versions[0]["id"]

        self.assertTrue(self.manager.rollback_to_version("r1", old_version))
        self.assertEqual(self.manager.load_result("r1").content, "Original")
        # Aktueller Stand vor Rollback wurde gesichert
        versions = self.manager.list_versions("r1")
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0]["note"], "Vor Wiederherstellung")

    def test_diff_versions(self):
        self.manager.update_result_content("r1", "Zeile 1\nZeile 2 geändert\n")
        version_id = self.manager.list_versions("r1")[0]["id"]
        diff = self.manager.diff_versions("r1", version_id, "current")
        self.assertIn("-Original", diff)
        self.assertIn("+Zeile 1", diff)

    def test_diff_unknown_version(self):
        self.assertIsNone(self.manager.diff_versions("r1", "nope", "current"))

    def test_delete_result_removes_versions(self):
        self.manager.update_result_content("r1", "Geändert")
        self.assertTrue(self.manager.delete_result("r1"))
        self.assertEqual(self.manager.list_versions("r1"), [])


if __name__ == "__main__":
    unittest.main()
