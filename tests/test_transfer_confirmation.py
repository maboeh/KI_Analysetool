import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import reset_usage_stats, set_session_budget
from transfer_confirmation import (
    TRANSFER_NOTICES,
    evaluate_transfer,
)


class TestEvaluateTransfer(unittest.TestCase):
    def tearDown(self):
        set_session_budget(None)
        reset_usage_stats()

    def test_clean_text_needs_no_confirmation(self):
        context = evaluate_transfer("Fasse diesen Text zusammen.", "website")
        self.assertFalse(context.needs_confirmation)
        self.assertEqual(context.notice, TRANSFER_NOTICES["website"])

    def test_findings_trigger_confirmation(self):
        context = evaluate_transfer("Mail an test@example.com", "default")
        self.assertTrue(context.needs_confirmation)
        self.assertTrue(context.report.has_findings)

    def test_pdf_always_needs_confirmation(self):
        context = evaluate_transfer("Analysiere das Dokument.", "pdf")
        self.assertTrue(context.needs_confirmation)
        self.assertIn("hochgeladen", context.notice)

    def test_privacy_check_disabled_skips_scan(self):
        context = evaluate_transfer("Mail an test@example.com", "default",
                                    privacy_check=False)
        self.assertFalse(context.report.has_findings)
        self.assertFalse(context.needs_confirmation)

    def test_budget_warning_triggers_confirmation(self):
        set_session_budget(0.0001)
        context = evaluate_transfer("Kurzer Text", "default")
        self.assertTrue(context.needs_confirmation)
        self.assertTrue(context.budget["projected_exceeded"])

    def test_estimate_included(self):
        context = evaluate_transfer("a" * 400, "default")
        self.assertGreater(context.estimated_cost, 0)
        self.assertEqual(context.estimated_input_tokens, 100)


if __name__ == "__main__":
    unittest.main()
