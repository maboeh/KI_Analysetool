"""
Tests for the ChartGenerator class.

This module contains comprehensive tests for chart generation functionality,
including chart type suggestion, chart creation, and export capabilities.
"""

import unittest
import tempfile
import os
import matplotlib.pyplot as plt
from unittest.mock import patch, MagicMock
from datetime import datetime

from chart_generator import ChartGenerator, ChartSuggestion, InteractiveChart
from data_models import (
    StructuredData, DataTable, NumericValue, TemporalValue, 
    ChartType, ChartConfig, Visualization, EntityType
)


class TestChartGenerator(unittest.TestCase):
    """Test cases for ChartGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = ChartGenerator()
        
        # Create sample data for testing
        self.sample_table = DataTable(
            headers=["Kategorie", "Wert"],
            rows=[
                ["A", "10"],
                ["B", "20"],
                ["C", "15"],
                ["D", "25"]
            ],
            title="Test Tabelle"
        )
        
        self.sample_numeric_values = [
            NumericValue(value=10.5, unit="€", context="Preis A"),
            NumericValue(value=20.0, unit="€", context="Preis B"),
            NumericValue(value=15.5, unit="€", context="Preis C"),
            NumericValue(value=25.0, unit="€", context="Preis D"),
            NumericValue(value=12.5, unit="€", context="Preis E")
        ]
        
        self.sample_temporal_data = [
            TemporalValue(
                value=datetime(2023, 1, 1),
                original_text="2023-01-01",
                precision="day"
            ),
            TemporalValue(
                value=datetime(2023, 2, 1),
                original_text="2023-02-01",
                precision="day"
            ),
            TemporalValue(
                value=datetime(2023, 3, 1),
                original_text="2023-03-01",
                precision="day"
            )
        ]
        
        self.sample_structured_data = StructuredData(
            tables=[self.sample_table],
            numeric_values=self.sample_numeric_values,
            temporal_data=self.sample_temporal_data
        )
    
    def test_initialization(self):
        """Test ChartGenerator initialization."""
        generator = ChartGenerator()
        
        self.assertIsInstance(generator.color_schemes, dict)
        self.assertIn('default', generator.color_schemes)
        self.assertIn('pastel', generator.color_schemes)
        self.assertIsInstance(generator.suggestion_rules, dict)
    
    def test_suggest_chart_types_with_table(self):
        """Test chart type suggestions for table data."""
        suggestions = self.generator.suggest_chart_types(self.sample_structured_data)
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        
        # Should suggest bar chart for mixed categorical/numeric data
        bar_suggestions = [s for s in suggestions if s.chart_type == ChartType.BAR]
        self.assertGreater(len(bar_suggestions), 0)
        
        # Check suggestion properties
        first_suggestion = suggestions[0]
        self.assertIsInstance(first_suggestion, ChartSuggestion)
        self.assertIsInstance(first_suggestion.confidence, float)
        self.assertGreater(first_suggestion.confidence, 0)
        self.assertLessEqual(first_suggestion.confidence, 1)
        self.assertIsInstance(first_suggestion.reasoning, str)
        self.assertIsInstance(first_suggestion.suggested_config, ChartConfig)
    
    def test_suggest_chart_types_with_numeric_values(self):
        """Test chart type suggestions for numeric values."""
        # Create data with only numeric values
        numeric_only_data = StructuredData(numeric_values=self.sample_numeric_values)
        
        suggestions = self.generator.suggest_chart_types(numeric_only_data)
        
        # Should suggest histogram for multiple numeric values
        histogram_suggestions = [s for s in suggestions if s.chart_type == ChartType.HISTOGRAM]
        self.assertGreater(len(histogram_suggestions), 0)
    
    def test_suggest_chart_types_with_temporal_data(self):
        """Test chart type suggestions for temporal data."""
        # Create data with only temporal values
        temporal_only_data = StructuredData(temporal_data=self.sample_temporal_data)
        
        suggestions = self.generator.suggest_chart_types(temporal_only_data)
        
        # Should suggest line chart for temporal data
        line_suggestions = [s for s in suggestions if s.chart_type == ChartType.LINE]
        self.assertGreater(len(line_suggestions), 0)
    
    def test_suggest_chart_types_empty_data(self):
        """Test chart type suggestions with empty data."""
        empty_data = StructuredData()
        
        suggestions = self.generator.suggest_chart_types(empty_data)
        
        self.assertEqual(len(suggestions), 0)
    
    def test_is_numeric_column(self):
        """Test numeric column detection."""
        # Numeric column
        numeric_data = ["10", "20.5", "15", "25.0"]
        self.assertTrue(self.generator._is_numeric_column(numeric_data))
        
        # Mixed column (should still be considered numeric if >70% numeric)
        mixed_data = ["10", "20", "15", "text"]
        self.assertTrue(self.generator._is_numeric_column(mixed_data))
        
        # Text column
        text_data = ["A", "B", "C", "D"]
        self.assertFalse(self.generator._is_numeric_column(text_data))
        
        # Empty column
        empty_data = []
        self.assertFalse(self.generator._is_numeric_column(empty_data))
    
    def test_create_bar_chart(self):
        """Test bar chart creation."""
        config = ChartConfig(title="Test Bar Chart")
        
        visualization = self.generator.create_chart(
            self.sample_structured_data,
            ChartType.BAR,
            config
        )
        
        self.assertIsInstance(visualization, Visualization)
        self.assertEqual(visualization.chart_type, ChartType.BAR)
        self.assertEqual(visualization.config.title, "Test Bar Chart")
        self.assertTrue(hasattr(visualization, '_figure'))
        
        # Clean up
        plt.close(visualization._figure)
    
    def test_create_pie_chart(self):
        """Test pie chart creation."""
        config = ChartConfig(title="Test Pie Chart")
        
        visualization = self.generator.create_chart(
            self.sample_structured_data,
            ChartType.PIE,
            config
        )
        
        self.assertIsInstance(visualization, Visualization)
        self.assertEqual(visualization.chart_type, ChartType.PIE)
        self.assertTrue(hasattr(visualization, '_figure'))
        
        # Clean up
        plt.close(visualization._figure)
    
    def test_create_line_chart(self):
        """Test line chart creation."""
        # Create data suitable for line chart
        line_table = DataTable(
            headers=["X", "Y"],
            rows=[
                ["1", "10"],
                ["2", "15"],
                ["3", "12"],
                ["4", "18"],
                ["5", "20"]
            ]
        )
        line_data = StructuredData(tables=[line_table])
        
        config = ChartConfig(title="Test Line Chart")
        
        visualization = self.generator.create_chart(
            line_data,
            ChartType.LINE,
            config
        )
        
        self.assertIsInstance(visualization, Visualization)
        self.assertEqual(visualization.chart_type, ChartType.LINE)
        self.assertTrue(hasattr(visualization, '_figure'))
        
        # Clean up
        plt.close(visualization._figure)
    
    def test_create_scatter_chart(self):
        """Test scatter plot creation."""
        # Create data suitable for scatter plot
        scatter_table = DataTable(
            headers=["X", "Y"],
            rows=[
                ["1.5", "10.2"],
                ["2.3", "15.1"],
                ["3.1", "12.8"],
                ["4.7", "18.5"],
                ["5.2", "20.1"]
            ]
        )
        scatter_data = StructuredData(tables=[scatter_table])
        
        config = ChartConfig(title="Test Scatter Plot")
        
        visualization = self.generator.create_chart(
            scatter_data,
            ChartType.SCATTER,
            config
        )
        
        self.assertIsInstance(visualization, Visualization)
        self.assertEqual(visualization.chart_type, ChartType.SCATTER)
        self.assertTrue(hasattr(visualization, '_figure'))
        
        # Clean up
        plt.close(visualization._figure)
    
    def test_create_histogram(self):
        """Test histogram creation."""
        config = ChartConfig(title="Test Histogram")
        
        visualization = self.generator.create_chart(
            self.sample_structured_data,
            ChartType.HISTOGRAM,
            config
        )
        
        self.assertIsInstance(visualization, Visualization)
        self.assertEqual(visualization.chart_type, ChartType.HISTOGRAM)
        self.assertTrue(hasattr(visualization, '_figure'))
        
        # Clean up
        plt.close(visualization._figure)
    
    def test_create_chart_with_invalid_type(self):
        """Test chart creation with invalid chart type."""
        with self.assertRaises(ValueError):
            # This should raise an error for unsupported chart type
            self.generator.create_chart(
                self.sample_structured_data,
                "invalid_type"  # This will cause an error
            )
    
    def test_create_chart_with_insufficient_data(self):
        """Test chart creation with insufficient data."""
        empty_data = StructuredData()
        
        with self.assertRaises(ValueError):
            self.generator.create_chart(
                empty_data,
                ChartType.BAR
            )
    
    def test_export_chart(self):
        """Test chart export functionality."""
        # Create a chart
        visualization = self.generator.create_chart(
            self.sample_structured_data,
            ChartType.BAR
        )
        
        # Test PNG export
        with tempfile.TemporaryDirectory() as temp_dir:
            png_path = os.path.join(temp_dir, "test_chart.png")
            
            success = self.generator.export_chart(visualization, png_path, format='png')
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(png_path))
            self.assertEqual(visualization.file_path, png_path)
        
        # Clean up
        plt.close(visualization._figure)
    
    def test_export_chart_pdf(self):
        """Test PDF chart export."""
        # Create a chart
        visualization = self.generator.create_chart(
            self.sample_structured_data,
            ChartType.PIE
        )
        
        # Test PDF export
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, "test_chart.pdf")
            
            success = self.generator.export_chart(visualization, pdf_path, format='pdf')
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(pdf_path))
        
        # Clean up
        plt.close(visualization._figure)
    
    def test_export_chart_without_figure(self):
        """Test export with visualization that has no figure."""
        visualization = Visualization(chart_type=ChartType.BAR)
        # No _figure attribute
        
        with tempfile.TemporaryDirectory() as temp_dir:
            png_path = os.path.join(temp_dir, "test_chart.png")
            
            success = self.generator.export_chart(visualization, png_path)
            
            self.assertFalse(success)
    
    def test_get_chart_as_bytes(self):
        """Test getting chart as bytes."""
        # Create a chart
        visualization = self.generator.create_chart(
            self.sample_structured_data,
            ChartType.BAR
        )
        
        # Get as bytes
        chart_bytes = self.generator.get_chart_as_bytes(visualization, format='png')
        
        self.assertIsInstance(chart_bytes, bytes)
        self.assertGreater(len(chart_bytes), 0)
        
        # Clean up
        plt.close(visualization._figure)
    
    def test_get_chart_as_bytes_without_figure(self):
        """Test getting bytes from visualization without figure."""
        visualization = Visualization(chart_type=ChartType.BAR)
        
        with self.assertRaises(ValueError):
            self.generator.get_chart_as_bytes(visualization)
    
    def test_create_interactive_chart(self):
        """Test interactive chart creation."""
        # Create a chart
        visualization = self.generator.create_chart(
            self.sample_structured_data,
            ChartType.BAR
        )
        
        # Create interactive version
        interactive_chart = self.generator.create_interactive_chart(visualization)
        
        self.assertIsInstance(interactive_chart, InteractiveChart)
        self.assertEqual(interactive_chart.visualization, visualization)
        
        # Clean up
        plt.close(visualization._figure)
    
    def test_analyze_table_for_charts_mixed_data(self):
        """Test table analysis for mixed categorical/numeric data."""
        suggestions = self.generator._analyze_table_for_charts(self.sample_table, "test_table")
        
        self.assertGreater(len(suggestions), 0)
        
        # Should suggest bar chart
        bar_suggestions = [s for s in suggestions if s.chart_type == ChartType.BAR]
        self.assertGreater(len(bar_suggestions), 0)
        
        # Should also suggest pie chart for small number of categories
        pie_suggestions = [s for s in suggestions if s.chart_type == ChartType.PIE]
        self.assertGreater(len(pie_suggestions), 0)
    
    def test_analyze_table_for_charts_numeric_only(self):
        """Test table analysis for numeric-only data."""
        numeric_table = DataTable(
            headers=["X", "Y"],
            rows=[
                ["1.5", "10.2"],
                ["2.3", "15.1"],
                ["3.1", "12.8"]
            ]
        )
        
        suggestions = self.generator._analyze_table_for_charts(numeric_table, "numeric_table")
        
        # Should suggest scatter plot
        scatter_suggestions = [s for s in suggestions if s.chart_type == ChartType.SCATTER]
        self.assertGreater(len(scatter_suggestions), 0)
    
    def test_analyze_table_for_charts_empty_table(self):
        """Test table analysis with empty table."""
        empty_table = DataTable(headers=[], rows=[])
        
        suggestions = self.generator._analyze_table_for_charts(empty_table, "empty_table")
        
        self.assertEqual(len(suggestions), 0)
    
    def test_extract_bar_chart_data(self):
        """Test bar chart data extraction."""
        data = self.generator._extract_bar_chart_data(self.sample_structured_data, "table_0")
        
        self.assertIsNotNone(data)
        labels, values = data
        
        self.assertEqual(len(labels), 4)
        self.assertEqual(len(values), 4)
        self.assertEqual(labels, ["A", "B", "C", "D"])
        self.assertEqual(values, [10.0, 20.0, 15.0, 25.0])
    
    def test_extract_line_chart_data_temporal(self):
        """Test line chart data extraction from temporal data."""
        data = self.generator._extract_line_chart_data(self.sample_structured_data, "temporal")
        
        self.assertIsNotNone(data)
        x_values, y_values = data
        
        self.assertEqual(len(x_values), 3)
        self.assertEqual(len(y_values), 3)
        self.assertEqual(y_values, [1, 2, 3])  # Event count
    
    def test_extract_histogram_data(self):
        """Test histogram data extraction."""
        values = self.generator._extract_histogram_data(self.sample_structured_data, "numeric")
        
        self.assertIsNotNone(values)
        self.assertGreater(len(values), 5)  # Should include both numeric_values and table data
    
    def test_chart_config_application(self):
        """Test that chart configuration is properly applied."""
        config = ChartConfig(
            title="Custom Title",
            x_label="Custom X",
            y_label="Custom Y",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        
        visualization = self.generator.create_chart(
            self.sample_structured_data,
            ChartType.BAR,
            config
        )
        
        self.assertEqual(visualization.config.title, "Custom Title")
        self.assertEqual(visualization.config.x_label, "Custom X")
        self.assertEqual(visualization.config.y_label, "Custom Y")
        self.assertEqual(visualization.config.colors, ["#FF0000", "#00FF00", "#0000FF"])
        
        # Clean up
        plt.close(visualization._figure)


class TestInteractiveChart(unittest.TestCase):
    """Test cases for InteractiveChart class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = ChartGenerator()
        
        # Create sample data
        sample_table = DataTable(
            headers=["Category", "Value"],
            rows=[["A", "10"], ["B", "20"]]
        )
        sample_data = StructuredData(tables=[sample_table])
        
        # Create visualization
        self.visualization = self.generator.create_chart(
            sample_data,
            ChartType.BAR
        )
        
        self.interactive_chart = InteractiveChart(self.visualization)
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.visualization, '_figure'):
            plt.close(self.visualization._figure)
    
    def test_initialization(self):
        """Test InteractiveChart initialization."""
        self.assertEqual(self.interactive_chart.visualization, self.visualization)
        self.assertIsNone(self.interactive_chart.canvas)
        self.assertIsNone(self.interactive_chart.toolbar)
    
    @patch('tkinter.Tk')
    def test_embed_in_tkinter(self, mock_tk):
        """Test embedding chart in Tkinter widget."""
        # Mock parent widget
        mock_parent = MagicMock()
        
        # This test would require actual Tkinter setup, so we'll just test the method exists
        self.assertTrue(hasattr(self.interactive_chart, 'embed_in_tkinter'))
        self.assertTrue(callable(self.interactive_chart.embed_in_tkinter))
    
    def test_embed_without_figure(self):
        """Test embedding chart without figure."""
        visualization_no_fig = Visualization(chart_type=ChartType.BAR)
        interactive_chart = InteractiveChart(visualization_no_fig)
        
        mock_parent = MagicMock()
        
        with self.assertRaises(ValueError):
            interactive_chart.embed_in_tkinter(mock_parent)


class TestChartSuggestion(unittest.TestCase):
    """Test cases for ChartSuggestion dataclass."""
    
    def test_chart_suggestion_creation(self):
        """Test ChartSuggestion creation and properties."""
        config = ChartConfig(title="Test")
        
        suggestion = ChartSuggestion(
            chart_type=ChartType.BAR,
            confidence=0.8,
            reasoning="Test reasoning",
            data_source="test_source",
            suggested_config=config
        )
        
        self.assertEqual(suggestion.chart_type, ChartType.BAR)
        self.assertEqual(suggestion.confidence, 0.8)
        self.assertEqual(suggestion.reasoning, "Test reasoning")
        self.assertEqual(suggestion.data_source, "test_source")
        self.assertEqual(suggestion.suggested_config, config)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)