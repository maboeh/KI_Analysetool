import unittest

from evidence import (
    STATUS_NOT_CHECKABLE, STATUS_PLAUSIBLE, STATUS_UNVERIFIED,
    STATUS_VERIFIED, SourceDocument, extract_citations, validate_evidence,
)


class TestExtractCitations(unittest.TestCase):

    def test_empty_input(self):
        self.assertEqual(extract_citations(""), [])
        self.assertEqual(extract_citations(None), [])

    def test_finds_german_quote(self):
        text = 'Der Bericht sagt „Die Umsätze stiegen im Jahr 2023 deutlich an“ weiter.'
        citations = extract_citations(text)
        quotes = [c for c in citations if c.kind == "quote"]
        self.assertEqual(len(quotes), 1)
        self.assertIn("Umsätze stiegen", quotes[0].text)

    def test_finds_page_reference(self):
        citations = extract_citations("Siehe Seite 42 im Dokument.")
        self.assertTrue(any(c.kind == "page" for c in citations))

    def test_finds_timestamp(self):
        citations = extract_citations("Ab 12:34 wird das Thema erklärt.")
        self.assertTrue(any(c.kind == "timestamp" for c in citations))

    def test_finds_section_reference(self):
        citations = extract_citations("Details in Abschnitt 3.2 aufgeführt.")
        self.assertTrue(any(c.kind == "section" for c in citations))


class TestValidateEvidence(unittest.TestCase):

    def test_verifies_verbatim_quote(self):
        source = "Das Unternehmen erzielte 2023 einen Rekordumsatz von 5 Mio. Euro."
        result = "Laut Quelle: „Das Unternehmen erzielte 2023 einen Rekordumsatz von 5 Mio. Euro“"
        report = validate_evidence(result, source)
        self.assertEqual(report.verified_count, 1)
        self.assertEqual(report.unverified_count, 0)

    def test_verifies_quote_with_whitespace_difference(self):
        source = "Das Unternehmen\nerzielte   2023 einen Rekordumsatz von 5 Mio. Euro."
        result = "Zitat: „Das Unternehmen erzielte 2023 einen Rekordumsatz von 5 Mio. Euro“"
        report = validate_evidence(result, source)
        self.assertEqual(report.verified_count, 1)

    def test_fabricated_quote_is_unverified(self):
        source = "Völlig anderer Inhalt ohne diesen Satz."
        result = "Zitat: „Dieser Satz kommt in der Quelle niemals vor, ehrlich nicht“"
        report = validate_evidence(result, source)
        self.assertEqual(report.unverified_count, 1)
        self.assertEqual(report.verified_count, 0)

    def test_page_reference_never_verified(self):
        source = "Beliebiger Quelltext ohne Seitenstruktur."
        result = "Siehe Seite 12 und Abschnitt 4."
        report = validate_evidence(result, source)
        for citation in report.citations:
            self.assertEqual(citation.status, STATUS_NOT_CHECKABLE)

    def test_missing_source_marks_not_checkable(self):
        result = "Zitat: „Ein langes wörtliches Zitat aus einer nicht verfügbaren Quelle“"
        report = validate_evidence(result, None)
        self.assertFalse(report.source_available)
        for citation in report.citations:
            self.assertEqual(citation.status, STATUS_NOT_CHECKABLE)

    def test_no_citations_empty_report(self):
        report = validate_evidence("Kurzer Text ohne Belege.", "Quelle")
        self.assertEqual(report.citations, [])


class TestSourceDocument(unittest.TestCase):
    """Seiten- und zeitbewusste Belegprüfung (F3)."""

    def _pdf_source(self):
        return SourceDocument(
            text="\n\n".join([
                "Inhalt der ersten Seite mit Details.",
                "Inhalt der zweiten Seite mit anderen Angaben.",
                "Inhalt der dritten Seite mit Fazit."]),
            pages=["Inhalt der ersten Seite mit Details.",
                   "Inhalt der zweiten Seite mit anderen Angaben.",
                   "Inhalt der dritten Seite mit Fazit."],
        )

    def test_quote_verified_with_page_number(self):
        source = self._pdf_source()
        result = ("Zitat: „Inhalt der zweiten Seite mit anderen Angaben.“ "
                  "steht im Dokument.")
        report = validate_evidence(result, source)
        quote = next(c for c in report.citations if c.kind == "quote")
        self.assertEqual(quote.status, STATUS_VERIFIED)
        self.assertIn("Seite 2", quote.source_excerpt)

    def test_valid_page_reference_is_plausible(self):
        report = validate_evidence("Siehe Seite 2.", self._pdf_source())
        page = next(c for c in report.citations if c.kind == "page")
        self.assertEqual(page.status, STATUS_PLAUSIBLE)

    def test_invalid_page_reference_is_unverified(self):
        report = validate_evidence("Siehe Seite 99.", self._pdf_source())
        page = next(c for c in report.citations if c.kind == "page")
        self.assertEqual(page.status, STATUS_UNVERIFIED)
        self.assertIn("erfundener Beleg", page.source_excerpt)

    def test_page_reference_without_structure_not_checkable(self):
        report = validate_evidence(
            "Siehe Seite 2.", SourceDocument(text="Fließtext ohne Seiten."))
        page = next(c for c in report.citations if c.kind == "page")
        self.assertEqual(page.status, STATUS_NOT_CHECKABLE)

    def test_valid_timestamp_is_plausible(self):
        source = SourceDocument(text="Transkript …", duration=600.0)
        report = validate_evidence("Ab 05:30 wird das Thema erklärt.", source)
        ts = next(c for c in report.citations if c.kind == "timestamp")
        self.assertEqual(ts.status, STATUS_PLAUSIBLE)

    def test_timestamp_beyond_duration_is_unverified(self):
        source = SourceDocument(text="Transkript …", duration=600.0)
        report = validate_evidence("Bei 15:00 passiert etwas.", source)
        ts = next(c for c in report.citations if c.kind == "timestamp")
        self.assertEqual(ts.status, STATUS_UNVERIFIED)
        self.assertIn("erfundener Beleg", ts.source_excerpt)

    def test_timestamp_without_duration_not_checkable(self):
        report = validate_evidence("Bei 05:30 passiert etwas.", "Nur Text.")
        ts = next(c for c in report.citations if c.kind == "timestamp")
        self.assertEqual(ts.status, STATUS_NOT_CHECKABLE)

    def test_plain_string_source_still_works(self):
        report = validate_evidence(
            "Zitat: „Ein langer wörtlicher Satz aus der Quelle\"",
            "Vorher. Ein langer wörtlicher Satz aus der Quelle. Nachher.")
        quote = next(c for c in report.citations if c.kind == "quote")
        self.assertEqual(quote.status, STATUS_VERIFIED)


if __name__ == "__main__":
    unittest.main()
