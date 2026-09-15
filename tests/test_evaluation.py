"""Tests für evaluation.py (Checks, Lauf, Bericht, Store, Parsing)."""

import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import AnalysisError, AnalysisErrorCode, AnalysisOutcome
from evaluation import (
    CaseResult,
    CheckResult,
    EvalCase,
    EvalRun,
    EvalSuite,
    EvaluationStore,
    Variant,
    parse_variant_lines,
    render_markdown_report,
    run_evaluation,
    score_output,
)
from evaluation_ui import format_expectations, parse_expectations


def _case(**kwargs):
    defaults = {"id": "c1", "name": "Fall", "input_text": "Eingabe"}
    defaults.update(kwargs)
    return EvalCase(**defaults)


def _outcome(content="", error=None, prompt_tokens=0, completion_tokens=0):
    return AnalysisOutcome(content=content, error=error,
                           prompt_tokens=prompt_tokens,
                           completion_tokens=completion_tokens)


class TestScoreOutput(unittest.TestCase):
    def test_must_contain_positive(self):
        case = _case(must_contain=["Digitalisierung"])
        checks = score_output("Die Digitalisierung wächst.", case)
        self.assertEqual(len(checks), 1)
        self.assertTrue(checks[0].passed)
        self.assertEqual(checks[0].name, "enthält: Digitalisierung")

    def test_must_contain_case_and_whitespace_tolerant(self):
        case = _case(must_contain=["neue   kompetenzen"])
        checks = score_output("Neue\nKompetenzen sind nötig.", case)
        self.assertTrue(checks[0].passed)

    def test_must_contain_negative(self):
        case = _case(must_contain=["fehlt"])
        checks = score_output("anderer Inhalt", case)
        self.assertFalse(checks[0].passed)
        self.assertIn("fehlt", checks[0].detail)

    def test_must_not_contain(self):
        case = _case(must_not_contain=["Fehler"])
        self.assertTrue(score_output("alles ok", case)[0].passed)
        self.assertFalse(score_output("Ein Fehler trat auf", case)[0].passed)

    def test_regex_match_and_miss(self):
        case = _case(regex=[r"\d{4}"])
        self.assertTrue(score_output("Jahr 2024", case)[0].passed)
        self.assertFalse(score_output("kein Jahr", case)[0].passed)
        self.assertEqual(score_output("kein Jahr", case)[0].detail,
                         "Kein Treffer")

    def test_regex_invalid(self):
        case = _case(regex=["[unclosed"])
        checks = score_output("irgendwas", case)
        self.assertFalse(checks[0].passed)
        self.assertEqual(checks[0].detail, "Ungültiger Ausdruck")

    def test_max_output_chars(self):
        case = _case(max_output_chars=10)
        self.assertTrue(score_output("kurz", case)[0].passed)
        content = "viel zu langer Output"
        checks = score_output(content, case)
        self.assertFalse(checks[0].passed)
        self.assertIn(str(len(content)), checks[0].detail)

    def test_expect_json_plain(self):
        case = _case(expect_json=True)
        self.assertTrue(score_output('{"a": 1}', case)[0].passed)
        self.assertFalse(score_output("kein json", case)[0].passed)

    def test_expect_json_fenced_block(self):
        case = _case(expect_json=True)
        content = 'Vorwort\n```json\n{"a": 1}\n```\nNachwort'
        self.assertTrue(score_output(content, case)[0].passed)

    def test_case_without_checks_passes_on_done(self):
        result = CaseResult(case_id="c1", variant_label="v", status="done",
                            content="x")
        self.assertTrue(result.passed)
        self.assertIsNone(result.check_pass_rate)


class TestParseVariantLines(unittest.TestCase):
    def test_model_and_prompt(self):
        variants = parse_variant_lines(
            "gpt-4o | Sag hallo\nNur ein Prompt",
            ["gpt-4o", "gpt-4o-mini"], "gpt-4o-mini")
        self.assertEqual(len(variants), 2)
        self.assertEqual(variants[0].model, "gpt-4o")
        self.assertEqual(variants[0].prompt, "Sag hallo")
        self.assertEqual(variants[1].model, "gpt-4o-mini")
        self.assertEqual(variants[1].prompt, "Nur ein Prompt")

    def test_empty_lines_and_missing_prompt_skipped(self):
        variants = parse_variant_lines("\n gpt-4o | \n", ["gpt-4o"], "gpt-4o")
        self.assertEqual(variants, [])


class TestRunEvaluation(unittest.TestCase):
    def setUp(self):
        self.suite = EvalSuite(
            id="s1", name="Suite", cases=[
                _case(id="c1", must_contain=["hallo"]),
                _case(id="c2", name="Zweiter", must_contain=["welt"]),
            ])
        self.variants = [
            Variant(label="v1", model="gpt-4o-mini", prompt="p1"),
            Variant(label="v2", model="gpt-4o-mini", prompt="p2"),
        ]

    def test_success_run(self):
        calls = []

        def analyze(content, prompt, model):
            calls.append((content, prompt, model))
            return _outcome("hallo welt", prompt_tokens=100,
                            completion_tokens=50)

        progress = []
        run = run_evaluation(self.suite, self.variants, analyze,
                             on_progress=lambda *a: progress.append(a))
        self.assertEqual(len(run.results), 4)
        self.assertTrue(all(r.status == "done" for r in run.results))
        self.assertTrue(all(r.passed for r in run.results))
        self.assertEqual(len(progress), 4)
        self.assertEqual(progress[-1][0], 4)
        self.assertEqual(progress[-1][1], 4)
        self.assertEqual(run.results[0].cost,
                         100 * 0.00015 / 1000 + 50 * 0.0006 / 1000)
        self.assertEqual(calls[0], ("Eingabe", "p1", "gpt-4o-mini"))

    def test_failed_outcome(self):
        def analyze(content, prompt, model):
            return _outcome(error=AnalysisError(
                AnalysisErrorCode.RATE_LIMITED, "Limit erreicht"))

        run = run_evaluation(self.suite, self.variants[:1], analyze)
        self.assertEqual(run.results[0].status, "failed")
        self.assertEqual(run.results[0].error_message, "Limit erreicht")
        self.assertFalse(run.results[0].passed)

    def test_cancel_stops_remaining(self):
        cancel = threading.Event()

        def analyze(content, prompt, model):
            return _outcome("hallo welt")

        def on_progress(done, total, result):
            cancel.set()

        run = run_evaluation(self.suite, self.variants[:1], analyze,
                             on_progress=on_progress, cancel_event=cancel)
        self.assertEqual(run.results[0].status, "done")
        self.assertEqual(run.results[1].status, "cancelled")

    def test_privacy_blocks_nonlocal_provider(self):
        suite = EvalSuite(id="s2", name="S", cases=[
            _case(input_text="Kontakt: max@example.com")])
        calls = []

        def analyze(content, prompt, model):
            calls.append(1)
            return _outcome("x")

        with patch("analysis.is_local_provider", return_value=False):
            run = run_evaluation(suite, self.variants[:1], analyze)
        self.assertEqual(run.results[0].status, "privacy_blocked")
        self.assertEqual(calls, [])

    def test_privacy_allows_local_provider(self):
        suite = EvalSuite(id="s3", name="S", cases=[
            _case(input_text="Kontakt: max@example.com")])
        calls = []

        def analyze(content, prompt, model):
            calls.append(1)
            return _outcome("hallo")

        with patch("analysis.is_local_provider", return_value=True):
            run = run_evaluation(suite, self.variants[:1], analyze)
        self.assertEqual(run.results[0].status, "done")
        self.assertEqual(run.results[0].cost, 0.0)
        self.assertEqual(len(calls), 1)

    def test_summary_and_best_variant(self):
        def analyze(content, prompt, model):
            if prompt == "p1":
                return _outcome("hallo welt", prompt_tokens=10,
                                completion_tokens=5)
            return _outcome("nichts passendes", prompt_tokens=200,
                            completion_tokens=100)

        run = run_evaluation(self.suite, self.variants, analyze)
        summaries = run.summary()
        self.assertEqual(summaries[0].cases_passed, 2)
        self.assertEqual(summaries[1].cases_passed, 0)
        self.assertEqual(summaries[0].check_pass_rate, 1.0)
        self.assertEqual(run.best_variant(), "v1")

    def test_best_variant_tie_breaks_on_tokens(self):
        def analyze(content, prompt, model):
            tokens = 10 if prompt == "p1" else 500
            return _outcome("hallo welt", prompt_tokens=tokens,
                            completion_tokens=0)

        run = run_evaluation(self.suite, self.variants, analyze)
        self.assertEqual(run.best_variant(), "v1")

    def test_best_variant_none_when_nothing_passed(self):
        def analyze(content, prompt, model):
            return _outcome("falsch")

        run = run_evaluation(self.suite, self.variants, analyze)
        self.assertIsNone(run.best_variant())


class TestMarkdownReport(unittest.TestCase):
    def test_report_contains_variants_and_best(self):
        suite = EvalSuite(id="s1", name="Meine Suite",
                          cases=[_case(must_contain=["hallo"])])
        variants = [Variant(label="v1", model="m", prompt="p")]
        run = EvalRun(id="r1", suite_id="s1", started_at="2025-01-01T10:00",
                      finished_at="2025-01-01T10:05", variants=variants,
                      results=[CaseResult(
                          case_id="c1", variant_label="v1", status="done",
                          content="hallo " * 100,
                          checks=[CheckResult("enthält: hallo", True)])])
        report = render_markdown_report(run, suite)
        self.assertIn("Meine Suite", report)
        self.assertIn("v1", report)
        self.assertIn("Beste Variante", report)
        self.assertNotIn("hallo " * 40, report)  # nur 200-Zeichen-Auszug


class TestEvaluationStore(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.db_path = str(self.tmp / "results.db")
        self.store = EvaluationStore(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _suite(self, suite_id="s1", name="Suite"):
        return EvalSuite(id=suite_id, name=name, cases=[
            _case(id="c1", must_contain=["x"])])

    def _run(self, run_id, suite_id="s1", started="2025-01-01T10:00"):
        return EvalRun(id=run_id, suite_id=suite_id, started_at=started,
                       finished_at=started, variants=[
                           Variant(label="v1", model="m", prompt="p")],
                       results=[CaseResult(case_id="c1", variant_label="v1",
                                           status="done", content="x")])

    def test_suite_roundtrip(self):
        suite = self._suite()
        self.store.save_suite(suite)
        loaded = self.store.get_suite("s1")
        self.assertEqual(loaded.name, "Suite")
        self.assertEqual(len(loaded.cases), 1)
        self.assertEqual(loaded.cases[0].must_contain, ["x"])
        self.assertEqual(len(self.store.list_suites()), 1)

    def test_run_roundtrip_and_list_order(self):
        self.store.save_suite(self._suite())
        self.store.save_run(self._run("r1", started="2025-01-01T10:00"))
        self.store.save_run(self._run("r2", started="2025-01-02T10:00"))
        runs = self.store.list_runs("s1")
        self.assertEqual([r.id for r in runs], ["r2", "r1"])
        loaded = self.store.get_run("r1")
        self.assertEqual(loaded.results[0].status, "done")
        self.assertEqual(loaded.variants[0].label, "v1")

    def test_delete_suite_cascades_runs(self):
        self.store.save_suite(self._suite())
        self.store.save_run(self._run("r1"))
        self.store.delete_suite("s1")
        self.assertIsNone(self.store.get_suite("s1"))
        self.assertIsNone(self.store.get_run("r1"))
        self.assertEqual(self.store.list_runs("s1"), [])

    def test_export_import_json_new_id(self):
        suite = self._suite()
        text = EvaluationStore.export_suite_json(suite)
        imported = EvaluationStore.import_suite_json(text)
        self.assertNotEqual(imported.id, suite.id)
        self.assertEqual(imported.name, suite.name)
        self.assertEqual(len(imported.cases), 1)

    def test_import_validation(self):
        with self.assertRaises(ValueError):
            EvaluationStore.import_suite_json(json.dumps({"name": ""}))
        with self.assertRaises(ValueError):
            EvaluationStore.import_suite_json(
                json.dumps({"name": "x", "cases": []}))


class TestExpectationSyntax(unittest.TestCase):
    def test_parse_all_kinds(self):
        parsed = parse_expectations(
            "enthält: Foo\nenthält nicht: Bar\nregex: \\d+\n"
            "max_zeichen: 800\njson\n")
        self.assertEqual(parsed["must_contain"], ["Foo"])
        self.assertEqual(parsed["must_not_contain"], ["Bar"])
        self.assertEqual(parsed["regex"], ["\\d+"])
        self.assertEqual(parsed["max_output_chars"], 800)
        self.assertTrue(parsed["expect_json"])

    def test_format_parse_roundtrip(self):
        case = _case(must_contain=["a"], must_not_contain=["b"],
                     regex=["\\d"], max_output_chars=100, expect_json=True)
        parsed = parse_expectations(format_expectations(case))
        self.assertEqual(parsed["must_contain"], case.must_contain)
        self.assertEqual(parsed["must_not_contain"], case.must_not_contain)
        self.assertEqual(parsed["regex"], case.regex)
        self.assertEqual(parsed["max_output_chars"], case.max_output_chars)
        self.assertEqual(parsed["expect_json"], case.expect_json)

    def test_unknown_line_raises(self):
        with self.assertRaises(ValueError):
            parse_expectations("quatschzeile")
        with self.assertRaises(ValueError):
            parse_expectations("max_zeichen: abc")


if __name__ == "__main__":
    unittest.main()
