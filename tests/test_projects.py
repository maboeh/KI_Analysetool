import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_models import ProcessedResult, ResultMetadata, SourceInfo
from projects import ProjectManager
from results_manager import ResultsManager


def _make_result(rid: str = "r1") -> ProcessedResult:
    return ProcessedResult(
        id=rid,
        content="Testinhalt",
        source_info=SourceInfo(type="text"),
        metadata=ResultMetadata(analysis_type="text"),
    )


class TestProjectManager(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.db_path = str(self.tmp / "results.db")
        self.results_dir = str(self.tmp / "results")
        self.results_manager = ResultsManager(self.db_path, self.results_dir)
        self.manager = ProjectManager(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_create_and_get(self):
        project = self.manager.create_project("Analyse Q3", "Quartalsberichte")
        self.assertIsNotNone(project.id)
        loaded = self.manager.get_project(project.id)
        self.assertEqual(loaded.name, "Analyse Q3")
        self.assertEqual(loaded.description, "Quartalsberichte")
        self.assertFalse(loaded.archived)

    def test_empty_name_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.create_project("   ")

    def test_list_excludes_archived(self):
        active = self.manager.create_project("Aktiv")
        archived = self.manager.create_project("Archiv")
        self.manager.set_archived(archived.id, True)

        names = [p.name for p in self.manager.list_projects()]
        self.assertEqual(names, ["Aktiv"])
        names_all = [p.name for p in self.manager.list_projects(include_archived=True)]
        self.assertEqual(sorted(names_all), ["Aktiv", "Archiv"])

    def test_update_project(self):
        project = self.manager.create_project("Alt")
        self.assertTrue(self.manager.update_project(project.id, name="Neu",
                                                    description="Beschreibung"))
        loaded = self.manager.get_project(project.id)
        self.assertEqual(loaded.name, "Neu")
        self.assertEqual(loaded.description, "Beschreibung")

    def test_assign_and_list_results(self):
        project = self.manager.create_project("Projekt")
        self.results_manager.save_result(_make_result("r1"))
        self.results_manager.save_result(_make_result("r2"))

        self.assertTrue(self.manager.assign_result("r1", project.id))
        ids = self.manager.get_project_result_ids(project.id)
        self.assertEqual(ids, ["r1"])

        # Zuordnung entfernen
        self.manager.assign_result("r1", None)
        self.assertEqual(self.manager.get_project_result_ids(project.id), [])

    def test_assign_unknown_project_rejected(self):
        self.results_manager.save_result(_make_result())
        with self.assertRaises(ValueError):
            self.manager.assign_result("r1", "nonexistent")

    def test_delete_keeps_results(self):
        project = self.manager.create_project("Wegwerf")
        self.results_manager.save_result(_make_result("r1"))
        self.manager.assign_result("r1", project.id)

        self.assertTrue(self.manager.delete_project(project.id))
        self.assertIsNone(self.manager.get_project(project.id))
        # Ergebnis bleibt erhalten, Zuordnung entfernt
        self.assertIsNotNone(self.results_manager.load_result("r1"))
        self.assertEqual(self.manager.get_project_result_ids(project.id), [])


if __name__ == "__main__":
    unittest.main()
