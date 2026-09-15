"""GUI-Tests für evaluation_ui.py (withdrawn Root, Temp-DB)."""

import os
import shutil
import sys
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import AnalysisOutcome
from evaluation import EvaluationStore
from evaluation_ui import CaseEditorDialog, EvaluationDialog


class TestEvaluationDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.store = EvaluationStore(str(self.tmp / "results.db"))
        self.calls = []

        def analyze(content, prompt, model):
            self.calls.append((content, prompt, model))
            return AnalysisOutcome(
                content="Die Digitalisierung wächst.",
                prompt_tokens=10, completion_tokens=5)

        self.dialog = EvaluationDialog(
            self.root, self.store, ["gpt-4o-mini"], analyze,
            "gpt-4o-mini", privacy_check=True)

    def tearDown(self):
        if self.dialog.winfo_exists():
            self.dialog.destroy()
        self.root.update()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _pump(self, condition, timeout=10.0):
        deadline = time.time() + timeout
        while not condition():
            self.root.update()
            if time.time() > deadline:
                self.fail("Timeout beim Warten auf den Dialog")
            time.sleep(0.02)

    def test_dialog_opens(self):
        self.assertTrue(self.dialog.winfo_exists())
        self.assertEqual(self.dialog.title(), "Evaluationssuite")

    def test_sample_suite_creates_two_cases(self):
        self.dialog._create_sample_suite()
        suites = self.store.list_suites()
        self.assertEqual(len(suites), 1)
        self.assertEqual(len(suites[0].cases), 2)
        self.assertEqual(self.suite_list_size(), 1)

    def suite_list_size(self):
        return self.dialog.suite_list.size()

    def test_case_editor_saves_parsed_expectations(self):
        saved = []
        editor = CaseEditorDialog(self.dialog, None, on_save=saved.append)
        editor.name_var.set("Testfall A")
        editor.input_text.insert("1.0", "Beispiel-Input")
        editor.expect_text.insert("1.0", "enthält: Foo\nmax_zeichen: 100")
        editor._save()
        self.assertEqual(len(saved), 1)
        case = saved[0]
        self.assertEqual(case.name, "Testfall A")
        self.assertEqual(case.input_text, "Beispiel-Input")
        self.assertEqual(case.must_contain, ["Foo"])
        self.assertEqual(case.max_output_chars, 100)

    def test_run_fills_result_tree_and_persists(self):
        self.dialog._create_sample_suite()
        self.dialog._start_run()
        self._pump(lambda: self.dialog._run is not None
                   or (self.dialog._worker is not None
                       and not self.dialog._worker.is_alive()))
        self._pump(lambda: self.dialog._run is not None, timeout=5.0)

        run = self.dialog._run
        self.assertIsNotNone(run)
        self.assertEqual(len(run.results), 2)
        top_level = self.dialog.result_tree.get_children()
        self.assertEqual(len(top_level), 1)
        children = self.dialog.result_tree.get_children(top_level[0])
        self.assertEqual(len(children), 2)
        self.assertEqual(len(self.calls), 2)
        runs = self.store.list_runs(run.suite_id)
        self.assertEqual(len(runs), 1)
        self.assertIsNotNone(self.store.get_run(runs[0].id))


if __name__ == "__main__":
    unittest.main()
