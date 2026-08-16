"""
Tests for the DataVisualizationPanel class.

This module contains comprehensive tests for the visualization panel
functionality, including chart display, customization, and export.
"""

import unittest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from datetime import datetime

from visualization_panel import DataVisualizationPanel, ChartCustomization, ChartExportDialog
from chart_generator import ChartGenerator
from data_models import (
    StructuredData, DataTable, NumericValue, ChartType, 
    ChartConfig, Visualization
)


class TestDataVisualizationPanel(unittest.TestCase):
    """Test cases for DataVisualizationPanel class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create root window for testing
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        
        # Create test data
        self.sample_table = DataTable(
            headers=["Kategorie", "Wert"],
            rows=[
                ["A", "10"],
                ["B", "20"],
                ["C", "15"]
            ],
            title="Test Tabelle"
        )
        
        self.sample_data = StructuredData(
            tables=[self.sample_table],
            numeric_values=[
                NumericValue(value=10, context="Test A"),
                NumericValue(value=20, context="Test B"),
                NumericValue(value=15, context="Test C")
            ]
        )
        
        # Create visualization panel
        self.panel = DataVisualizationPanel(self.root)
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass  # Window already destroyed
    
    def test_initialization(self):
        """Test DataVisualizationPanel initialization."""
        self.assertIsInstance(self.panel.chart_generator, ChartGenerator)
        self.assertIsInstance(self.panel.customization, ChartCustomization)
        self.assertIsNone(self.panel.current_data)
        self.assertIsNone(self.panel.current_visualization)
        
        # Check UI components exist
        self.assertIsNotNone(self.panel.main_frame)
        self.assertIsNotNone(self.panel.notebook)
        self.assertIsNotNone(self.panel.chart_frame)
        self.assertIsNotNone(self.panel.custom_frame)
        self.assertIsNotNone(self.panel.suggestions_frame)
    
    def test_load_data(self):
        """Test loading data into the panel."""
        # Load data
        self.panel.load_data(self.sample_data)
        
        # Check data is stored
        self.assertEqual(self.panel.current_data, self.sample_data)
    
    def test_load_empty_data(self):
        """Test loading empty data."""
        empty_data = StructuredData()
        
        # Load empty data
        self.panel.load_data(empty_data)
        
        # Check data is stored but no chart is created
        self.assertEqual(self.panel.current_data, empty_data)
        self.assertIsNone(self.panel.current_visualization)
    
    def test_chart_customization_initialization(self):
        """Test ChartCustomization initialization."""
        customization = ChartCustomization()
        
        self.assertEqual(customization.title, "")
        self.assertEqual(customization.x_label, "")
        self.assertEqual(customization.y_label, "")
        self.assertEqual(customization.color_scheme, "default")
        self.assertEqual(customization.chart_style, "seaborn-v0_8")
        self.assertEqual(customization.width, 10)
        self.assertEqual(customization.height, 6)
        self.assertTrue(customization.show_grid)
        self.assertTrue(customization.show_legend)
    
    def test_get_current_config(self):
        """Test getting current chart configuration."""
        # Set some values
        self.panel.title_var.set("Test Title")
        self.panel.x_label_var.set("X Label")
        self.panel.y_label_var.set("Y Label")
        self.panel.width_var.set(12)
        self.panel.height_var.set(8)
        
        config = self.panel._get_current_config()
        
        self.assertIsInstance(config, ChartConfig)
        self.assertEqual(config.title, "Test Title")
        self.assertEqual(config.x_label, "X Label")
        self.assertEqual(config.y_label, "Y Label")
        self.assertEqual(config.size, (12, 8))
    
    def test_chart_type_selection(self):
        """Test chart type selection functionality."""
        # Test initial value
        self.assertEqual(self.panel.chart_type_var.get(), "BAR")
        
        # Test changing chart type
        self.panel.chart_type_var.set("PIE")
        self.assertEqual(self.panel.chart_type_var.get(), "PIE")
    
    @patch('tkinter.filedialog.asksaveasfilename')
    @patch('tkinter.messagebox.showinfo')
    def test_export_chart_success(self, mock_showinfo, mock_filedialog):
        """Test successful chart export."""
        # Setup mock
        mock_filedialog.return_value = "/tmp/test_chart.png"
        
        # Create a mock visualization with figure
        mock_visualization = Mock()
        mock_visualization._figure = Mock()
        self.panel.current_visualization = mock_visualization
        
        # Mock the chart generator export method
        with patch.object(self.panel.chart_generator, 'export_chart', return_value=True):
            # Test export
            self.panel._export_chart('png')
            
            # Verify file dialog was called
            mock_filedialog.assert_called_once()
            
            # Verify success message
            mock_showinfo.assert_called_once()
    
    @patch('tkinter.filedialog.asksaveasfilename')
    @patch('tkinter.messagebox.showwarning')
    def test_export_chart_no_visualization(self, mock_showwarning, mock_filedialog):
        """Test export when no visualization is available."""
        # Ensure no current visualization
        self.panel.current_visualization = None
        
        # Test export
        self.panel._export_chart('png')
        
        # Verify warning message
        mock_showwarning.assert_called_once_with("Warnung", "Kein Diagramm zum Exportieren verfügbar.")
        
        # Verify file dialog was not called
        mock_filedialog.assert_not_called()
    
    @patch('tkinter.filedialog.asksaveasfilename')
    def test_export_chart_cancelled(self, mock_filedialog):
        """Test export when user cancels file dialog."""
        # Setup mock to return empty string (cancelled)
        mock_filedialog.return_value = ""
        
        # Create a mock visualization
        self.panel.current_visualization = Mock()
        
        # Test export
        self.panel._export_chart('png')
        
        # Verify file dialog was called but no further action taken
        mock_filedialog.assert_called_once()
    
    def test_clear_functionality(self):
        """Test clearing the panel."""
        # Load some data first
        self.panel.load_data(self.sample_data)
        
        # Clear the panel
        self.panel.clear()
        
        # Verify everything is cleared
        self.assertIsNone(self.panel.current_data)
        self.assertIsNone(self.panel.current_visualization)
    
    def test_apply_customization(self):
        """Test applying customization settings."""
        # Set customization values
        self.panel.title_var.set("Custom Title")
        self.panel.x_label_var.set("Custom X")
        self.panel.y_label_var.set("Custom Y")
        self.panel.color_scheme_var.set("pastel")
        self.panel.width_var.set(15)
        self.panel.height_var.set(10)
        
        # Apply customization
        self.panel._apply_customization()
        
        # Check customization object is updated
        self.assertEqual(self.panel.customization.title, "Custom Title")
        self.assertEqual(self.panel.customization.x_label, "Custom X")
        self.assertEqual(self.panel.customization.y_label, "Custom Y")
        self.assertEqual(self.panel.customization.color_scheme, "pastel")
        self.assertEqual(self.panel.customization.width, 15)
        self.assertEqual(self.panel.customization.height, 10)
    
    @patch('tkinter.messagebox.showerror')
    def test_show_error_message(self, mock_showerror):
        """Test error message display."""
        error_msg = "Test error message"
        
        self.panel._show_error_message(error_msg)
        
        mock_showerror.assert_called_once_with("Fehler", error_msg)
    
    def test_get_current_visualization(self):
        """Test getting current visualization."""
        # Initially should be None
        self.assertIsNone(self.panel.get_current_visualization())
        
        # Set a mock visualization
        mock_viz = Mock()
        self.panel.current_visualization = mock_viz
        
        # Should return the mock visualization
        self.assertEqual(self.panel.get_current_visualization(), mock_viz)
    
    def test_callback_functionality(self):
        """Test callback functionality when chart is created."""
        callback_mock = Mock()
        
        # Create panel with callback
        panel_with_callback = DataVisualizationPanel(self.root, on_chart_created=callback_mock)
        
        # Verify callback is stored
        self.assertEqual(panel_with_callback.on_chart_created, callback_mock)
    
    @patch('visualization_panel.ChartGenerator')
    def test_chart_generator_integration(self, mock_chart_generator_class):
        """Test integration with ChartGenerator."""
        mock_generator = Mock()
        mock_chart_generator_class.return_value = mock_generator
        
        # Create new panel
        panel = DataVisualizationPanel(self.root)
        
        # Verify ChartGenerator was instantiated
        mock_chart_generator_class.assert_called_once()
        self.assertEqual(panel.chart_generator, mock_generator)
    
    def test_ui_component_creation(self):
        """Test that all UI components are created properly."""
        # Check main components exist
        self.assertTrue(hasattr(self.panel, 'main_frame'))
        self.assertTrue(hasattr(self.panel, 'notebook'))
        self.assertTrue(hasattr(self.panel, 'chart_frame'))
        self.assertTrue(hasattr(self.panel, 'custom_frame'))
        self.assertTrue(hasattr(self.panel, 'suggestions_frame'))
        
        # Check control variables exist
        self.assertTrue(hasattr(self.panel, 'chart_type_var'))
        self.assertTrue(hasattr(self.panel, 'title_var'))
        self.assertTrue(hasattr(self.panel, 'x_label_var'))
        self.assertTrue(hasattr(self.panel, 'y_label_var'))
        self.assertTrue(hasattr(self.panel, 'width_var'))
        self.assertTrue(hasattr(self.panel, 'height_var'))
    
    def test_chart_type_combo_values(self):
        """Test chart type combobox has correct values."""
        expected_values = ["BAR", "LINE", "PIE", "SCATTER", "HISTOGRAM"]
        actual_values = list(self.panel.chart_type_combo['values'])
        
        self.assertEqual(actual_values, expected_values)


class TestChartExportDialog(unittest.TestCase):
    """Test cases for ChartExportDialog class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        
        # Create mock visualization
        self.mock_visualization = Mock(spec=Visualization)
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass  # Window already destroyed
    
    def test_initialization(self):
        """Test ChartExportDialog initialization."""
        dialog = ChartExportDialog(self.root, self.mock_visualization)
        
        self.assertEqual(dialog.parent, self.root)
        self.assertEqual(dialog.visualization, self.mock_visualization)
        self.assertIsNone(dialog.result)
        
        # Check dialog window exists
        self.assertIsNotNone(dialog.dialog)
        self.assertEqual(dialog.dialog.title(), "Diagramm Export Optionen")
    
    def test_default_values(self):
        """Test default export dialog values."""
        dialog = ChartExportDialog(self.root, self.mock_visualization)
        
        # Check default values
        self.assertEqual(dialog.format_var.get(), "png")
        self.assertEqual(dialog.dpi_var.get(), 300)
        self.assertEqual(dialog.width_var.get(), 10.0)
        self.assertEqual(dialog.height_var.get(), 6.0)
    
    def test_export_result(self):
        """Test export dialog result generation."""
        dialog = ChartExportDialog(self.root, self.mock_visualization)
        
        # Set some values
        dialog.format_var.set("pdf")
        dialog.dpi_var.set(600)
        dialog.width_var.set(12.0)
        dialog.height_var.set(8.0)
        
        # Simulate export button click
        dialog._export()
        
        # Check result
        expected_result = {
            'format': 'pdf',
            'dpi': 600,
            'size': (12.0, 8.0)
        }
        self.assertEqual(dialog.result, expected_result)
    
    def test_cancel_result(self):
        """Test cancel dialog result."""
        dialog = ChartExportDialog(self.root, self.mock_visualization)
        
        # Simulate cancel button click
        dialog._cancel()
        
        # Check result is None
        self.assertIsNone(dialog.result)


class TestVisualizationPanelIntegration(unittest.TestCase):
    """Integration tests for visualization panel with real data."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        
        # Create realistic test data
        self.sales_table = DataTable(
            headers=["Monat", "Umsatz", "Kosten"],
            rows=[
                ["Januar", "10000", "7000"],
                ["Februar", "12000", "8000"],
                ["März", "15000", "9000"],
                ["April", "11000", "7500"]
            ],
            title="Monatliche Verkaufsdaten"
        )
        
        self.sales_data = StructuredData(
            tables=[self.sales_table],
            numeric_values=[
                NumericValue(value=10000, unit="€", context="Januar Umsatz"),
                NumericValue(value=12000, unit="€", context="Februar Umsatz"),
                NumericValue(value=15000, unit="€", context="März Umsatz"),
                NumericValue(value=11000, unit="€", context="April Umsatz")
            ]
        )
        
        self.panel = DataVisualizationPanel(self.root)
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass
    
    def test_realistic_data_loading(self):
        """Test loading realistic business data."""
        # Load the sales data
        self.panel.load_data(self.sales_data)
        
        # Verify data is loaded
        self.assertEqual(self.panel.current_data, self.sales_data)
        
        # Verify data is considered visualizable
        self.assertTrue(self.sales_data.has_visualizable_data())
    
    @patch('matplotlib.pyplot.show')  # Prevent actual plot display during tests
    def test_chart_creation_with_realistic_data(self, mock_show):
        """Test creating charts with realistic data."""
        # Load data
        self.panel.load_data(self.sales_data)
        
        # Try to create a bar chart
        try:
            config = ChartConfig(title="Test Sales Chart")
            self.panel._create_chart(ChartType.BAR, config)
            
            # Should have created a visualization
            self.assertIsNotNone(self.panel.current_visualization)
            self.assertEqual(self.panel.current_visualization.chart_type, ChartType.BAR)
            
        except Exception as e:
            self.fail(f"Chart creation failed with realistic data: {e}")
    
    def test_suggestions_with_realistic_data(self):
        """Test chart suggestions with realistic data."""
        # Load data
        self.panel.load_data(self.sales_data)
        
        # Get suggestions from chart generator
        suggestions = self.panel.chart_generator.suggest_chart_types(self.sales_data)
        
        # Should have suggestions for this type of data
        self.assertGreater(len(suggestions), 0)
        
        # Should suggest bar chart for categorical/numeric data
        chart_types = [s.chart_type for s in suggestions]
        self.assertIn(ChartType.BAR, chart_types)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)