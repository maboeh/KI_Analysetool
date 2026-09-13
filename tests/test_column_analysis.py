import unittest

from column_analysis import (
    analyze_columns, clean_column, is_missing, suggest_charts,
)
from data_models import DataTable


def make_table(headers, rows):
    return DataTable(headers=headers, rows=rows)


class TestAnalyzeColumns(unittest.TestCase):

    def test_numeric_column_german_format(self):
        table = make_table(["Betrag"], [["1.234,56"], ["2.000,00"], ["500,75"]])
        profiles = analyze_columns(table)
        self.assertEqual(profiles[0].role, "numeric")

    def test_date_column(self):
        table = make_table(["Datum"], [["01.01.2024"], ["15.03.2024"], ["2024-06-01"]])
        profiles = analyze_columns(table)
        self.assertEqual(profiles[0].role, "date")

    def test_categorical_column(self):
        table = make_table(
            ["Kategorie"], [["A"], ["B"], ["A"], ["B"], ["A"], ["B"], ["A"], ["B"]])
        profiles = analyze_columns(table)
        self.assertEqual(profiles[0].role, "categorical")

    def test_text_column(self):
        table = make_table(
            ["Beschreibung"],
            [[f"Ein einzigartiger langer Text Nummer {i} mit vielen Worten"]
             for i in range(20)])
        profiles = analyze_columns(table)
        self.assertEqual(profiles[0].role, "text")

    def test_missing_values_counted(self):
        table = make_table(["Wert"], [["5"], ["n/a"], [""], ["7"]])
        profiles = analyze_columns(table)
        self.assertEqual(profiles[0].missing, 2)
        self.assertEqual(profiles[0].total, 4)


class TestCleanColumn(unittest.TestCase):

    def test_drop_missing(self):
        self.assertEqual(clean_column(["1", "x", "3"], "drop_missing"),
                         [1.0, None, 3.0])

    def test_zero(self):
        self.assertEqual(clean_column(["1", "x"], "zero"), [1.0, 0.0])

    def test_mean(self):
        self.assertEqual(clean_column(["2", "x", "4"], "mean"), [2.0, 3.0, 4.0])

    def test_unknown_strategy(self):
        with self.assertRaises(ValueError):
            clean_column(["1"], "bogus")


class TestSuggestCharts(unittest.TestCase):

    def test_line_for_date_plus_numeric(self):
        table = make_table(
            ["Datum", "Umsatz"],
            [["01.01.2024", "100"], ["02.01.2024", "200"], ["03.01.2024", "150"]])
        suggestions = suggest_charts(table)
        self.assertTrue(any(s.chart_type == "line" for s in suggestions))
        line = next(s for s in suggestions if s.chart_type == "line")
        self.assertEqual(line.x_column, "Datum")
        self.assertIn("Umsatz", line.y_columns)
        self.assertTrue(line.reason)

    def test_bar_for_categorical_plus_numeric(self):
        table = make_table(
            ["Land", "Wert"],
            [["DE", "10"], ["FR", "20"], ["IT", "30"]])
        suggestions = suggest_charts(table)
        self.assertTrue(any(s.chart_type == "bar" for s in suggestions))

    def test_pie_for_few_categories(self):
        table = make_table(
            ["Land", "Wert"],
            [["DE", "10"], ["FR", "20"], ["IT", "30"]])
        suggestions = suggest_charts(table)
        self.assertTrue(any(s.chart_type == "pie" for s in suggestions))

    def test_scatter_for_two_numeric(self):
        table = make_table(
            ["Beschreibung", "A", "B"],
            [[f"Eintrag mit einzigartigem Text {i}", str(i), str(i * 2)]
             for i in range(20)])
        suggestions = suggest_charts(table)
        self.assertTrue(any(s.chart_type == "scatter" for s in suggestions))

    def test_missing_value_hint_present(self):
        table = make_table(
            ["Datum", "Wert"],
            [["01.01.2024", "100"], ["02.01.2024", "n/a"], ["03.01.2024", "150"]])
        suggestions = suggest_charts(table)
        self.assertTrue(any(s.missing_value_hint for s in suggestions))

    def test_too_few_rows_no_suggestions(self):
        table = make_table(["A"], [["x"]])
        self.assertEqual(suggest_charts(table), [])


class TestIsMissing(unittest.TestCase):

    def test_missing_markers(self):
        for value in [None, "", "-", "n/a", "N/A", "null", "?"]:
            self.assertTrue(is_missing(value), value)

    def test_real_value(self):
        self.assertFalse(is_missing("42"))


if __name__ == "__main__":
    unittest.main()
