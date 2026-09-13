import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from privacy_scanner import PrivacyReport, redact_text, scan_text


class TestPrivacyScanner(unittest.TestCase):
    def test_clean_text_has_no_findings(self):
        report = scan_text("Fasse den folgenden Artikel über Künstliche Intelligenz zusammen.")
        self.assertFalse(report.has_findings)

    def test_empty_input_returns_empty_report(self):
        for value in ("", "   ", None):
            report = scan_text(value)
            self.assertIsInstance(report, PrivacyReport)
            self.assertFalse(report.has_findings)

    def test_detects_email(self):
        report = scan_text("Kontakt: max.mustermann@example.com für Rückfragen.")
        self.assertTrue(report.has_findings)
        self.assertEqual(report.findings[0].kind, "email")
        self.assertIn("***", report.findings[0].masked_preview)
        self.assertNotIn("mustermann", report.findings[0].masked_preview)

    def test_detects_openai_key(self):
        report = scan_text("Hier ist der Key: sk-abcDEF1234567890xyzUVW bitte testen.")
        self.assertTrue(report.has_findings)
        self.assertEqual(report.findings[0].kind, "api_key")

    def test_detects_secret_assignment(self):
        report = scan_text("password = supergeheim123\nBitte analysiere die Config.")
        kinds = [f.kind for f in report.findings]
        self.assertIn("secret_assignment", kinds)

    def test_detects_valid_iban(self):
        report = scan_text("Überweise auf DE44 5001 0517 5407 3249 31 bitte.")
        kinds = [f.kind for f in report.findings]
        self.assertIn("iban", kinds)

    def test_invalid_iban_not_reported(self):
        report = scan_text("Die Nummer DE00 0000 0000 0000 0000 00 ist ungültig.")
        kinds = [f.kind for f in report.findings]
        self.assertNotIn("iban", kinds)

    def test_detects_valid_credit_card(self):
        # Luhn-gültige Testnummer (Visa-Testmuster)
        report = scan_text("Karte: 4111 1111 1111 1111")
        kinds = [f.kind for f in report.findings]
        self.assertIn("credit_card", kinds)

    def test_invalid_credit_card_not_reported(self):
        report = scan_text("Zahl: 4111 1111 1111 1112 ist keine echte Karte.")
        kinds = [f.kind for f in report.findings]
        self.assertNotIn("credit_card", kinds)

    def test_detects_international_phone(self):
        report = scan_text("Ruf an: +49 30 901820 für Details.")
        kinds = [f.kind for f in report.findings]
        self.assertIn("phone", kinds)

    def test_redact_replaces_all_findings(self):
        text = "Mail an test@example.com, Key sk-abcDEF1234567890xyzUVW."
        report = scan_text(text)
        redacted = redact_text(text, report)
        self.assertNotIn("test@example.com", redacted)
        self.assertNotIn("sk-abcDEF1234567890xyzUVW", redacted)
        self.assertIn("[E-Mail-Adresse entfernt]", redacted)
        self.assertIn("[API-Schlüssel / Token entfernt]", redacted)

    def test_redact_without_report_scans_internally(self):
        text = "Mail: a@b.de"
        redacted = redact_text(text)
        self.assertNotIn("a@b.de", redacted)

    def test_overlapping_findings_deduplicated(self):
        # Ein Secret-Assignment, das eine E-Mail enthält, soll nur einen Fund erzeugen
        report = scan_text("api_key = user@example.com12345678")
        starts = [f.start for f in report.findings]
        self.assertEqual(len(starts), len(set(starts)))

    def test_count_by_kind(self):
        report = scan_text("a@b.de und c@d.de")
        self.assertEqual(report.count_by_kind().get("email"), 2)


if __name__ == "__main__":
    unittest.main()
