import os
import sys
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import (
    AnalysisSession,
    AVAILABLE_MODELS,
    estimate_request_cost,
    get_budget_status,
    reset_usage_stats,
    set_session_budget,
)


class TestCostEstimate(unittest.TestCase):
    def test_estimate_uses_model_pricing(self):
        estimate = estimate_request_cost("a" * 4000, model="gpt-4o-mini")
        info = AVAILABLE_MODELS["gpt-4o-mini"]
        expected = (1000 * info["cost_per_1k_input"] +
                    1024 * info["cost_per_1k_output"]) / 1000
        self.assertAlmostEqual(estimate["estimated_cost"], expected, places=6)
        self.assertEqual(estimate["input_tokens"], 1000)
        self.assertEqual(estimate["model"], "gpt-4o-mini")

    def test_estimate_empty_text(self):
        estimate = estimate_request_cost("")
        self.assertGreaterEqual(estimate["input_tokens"], 1)
        self.assertGreater(estimate["estimated_cost"], 0)

    def test_unknown_model_falls_back(self):
        estimate = estimate_request_cost("test", model="nonexistent")
        self.assertGreater(estimate["estimated_cost"], 0)


class TestSessionBudget(unittest.TestCase):
    def setUp(self):
        self.session = AnalysisSession()

    def test_no_budget_by_default(self):
        status = self.session.get_budget_status()
        self.assertIsNone(status["limit"])
        self.assertFalse(status["warning"])
        self.assertFalse(status["exceeded"])

    def test_budget_thresholds(self):
        self.session.set_budget(1.0)
        self.session.total_cost_estimate = 0.5
        status = self.session.get_budget_status()
        self.assertFalse(status["warning"])

        self.session.total_cost_estimate = 0.85
        status = self.session.get_budget_status()
        self.assertTrue(status["warning"])
        self.assertFalse(status["exceeded"])

        self.session.total_cost_estimate = 1.05
        status = self.session.get_budget_status()
        self.assertTrue(status["exceeded"])

    def test_zero_or_negative_budget_disables(self):
        self.session.set_budget(1.0)
        self.session.set_budget(0)
        self.assertIsNone(self.session.get_budget_status()["limit"])
        self.session.set_budget(-5)
        self.assertIsNone(self.session.get_budget_status()["limit"])
        self.session.set_budget(None)
        self.assertIsNone(self.session.get_budget_status()["limit"])

    def test_module_level_budget_functions(self):
        try:
            set_session_budget(2.5)
            status = get_budget_status()
            self.assertEqual(status["limit"], 2.5)
        finally:
            set_session_budget(None)
            reset_usage_stats()

    def test_thread_safe_record_usage(self):
        session = AnalysisSession()
        errors = []

        def worker():
            try:
                for _ in range(100):
                    session.record_usage(10, 5)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertFalse(errors)
        stats = session.get_usage_stats()
        self.assertEqual(stats["total_tokens"], 8 * 100 * 15)


if __name__ == "__main__":
    unittest.main()
