"""
Tests for the ResultsBrowser GUI component.

This module contains tests for the results browser interface,
including filtering, searching, and management functionality.
"""

import unittest
import tempfile
import shutil
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from results_browser import ResultsBrowser, ExportFormatDialog, ComparisonWindow, StatisticsWindow
from results_manager import ResultsManager
from data_models import (
    ProcessedResult, SourceInfo, ResultMetadata, StructuredData,
    DataTable, ResultSummary
)


class TestResultsBrowser(unittest.TestCase):
    """Test cases for ResultsBrowser functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary database and directory
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = f"{self.temp_dir}/test_results.db"
        self.results_dir = f"{self.temp_dir}/test_results"
        
        # Create results manager
        self.results_manager = ResultsManager(self.db_path, self.results_dir)
        
        # Create root window for testing
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
        # Create test results
        self._create_test_results()
        
        # Mock callback
        self.mock_callback = Mock()
        
        # Create browser instance
        self.browser = ResultsBrowser(
            self.root, 
            self.results_manager, 
            self.mock_callback
        )
    
    def tearDown(self):
        """Clean up test environment."""
        try:
            self.root.destroy()
        except:
            pass
        shutil.rmtree(self.temp_dir)
    
    def _create_test_results(self):
        """Create sample test results."""
        # Result 1: Website analysis
        result1 = ProcessedResult(
            content="Website analysis content",
            source_info=SourceInfo(type="website", url="https://example.com"),
            metadata=ResultMetadata(analysis_type="zusammenfassung", tags=["web", "test"])
        )
        result1.created_at = datetime.now() - timedelta(days=1)
        self.results_manager.save_result(result1, "Website Analysis")
        
        # Result 2: Excel analysis with table
        structured_data = StructuredData()
        table = DataTable(
            headers=["Name", "Value"],
            rows=[["Item 1", "100"], ["Item 2", "200"]],
            title="Test Table"
        )
        structured_data.tables.append(table)
        
        result2 = ProcessedResult(
            content="Excel analysis with data",
            source_info=SourceInfo(type="excel", file_name="test.xlsx"),
            extracted_data=structured_data,
            metadata=ResultMetadata(analysis_type="datenextraktion", tags=["excel", "data"])
        )
        result2.created_at = datetime.now() - timedelta(hours=2)
        self.results_manager.save_result(result2, "Excel Data Analysis")
        
        # Result 3: Old PDF analysis
        result3 = ProcessedResult(
            content="Old PDF content",
            source_info=SourceInfo(type="pdf", file_name="old.pdf"),
            metadata=ResultMetadata(analysis_type="zusammenfassung", tags=["pdf", "old"])
        )
        result3.created_at = datetime.now() - timedelta(days=30)
        self.results_manager.save_result(result3, "Old PDF Analysis")
    
    def test_browser_initialization(self):
        """Test that browser initializes correctly."""
        self.assertIsNotNone(self.browser.main_frame)
        self.assertIsNotNone(self.browser.results_tree)
        self.assertIsNotNone(self.browser.results_manager)
        self.assertEqual(len(self.browser.current_results), 3)  # Should load all test results
    
    def test_results_display(self):
        """Test that results are displayed correctly in the tree."""
        # Check that all results are displayed
        tree_items = self.browser.results_tree.get_children()
        self.assertEqual(len(tree_items), 3)
        
        # Check first item content
        first_item = tree_items[0]
        values = self.browser.results_tree.item(first_item, 'values')
        self.assertIn("Excel Data Analysis", values[0])  # Should be newest first
    
    def test_search_functionality(self):
        """Test search filtering."""
        # Search for "Excel"
        self.browser.search_var.set("Excel")
        self.browser._load_results()
        
        # Should find only the Excel result
        self.assertEqual(len(self.browser.current_results), 1)
        self.assertIn("Excel", self.browser.current_results[0].title)
    
    def test_analysis_type_filter(self):
        """Test filtering by analysis type."""
        # Set filter to "zusammenfassung"
        self.browser.analysis_type_var.set("zusammenfassung")
        self.browser._load_results()
        
        # Should find 2 results with "zusammenfassung" type
        self.assertEqual(len(self.browser.current_results), 2)
        for result in self.browser.current_results:
            self.assertEqual(result.analysis_type, "zusammenfassung")
    
    def test_source_type_filter(self):
        """Test filtering by source type."""
        # Set filter to "excel"
        self.browser.source_type_var.set("excel")
        self.browser._load_results()
        
        # Should find only the Excel result
        self.assertEqual(len(self.browser.current_results), 1)
        self.assertEqual(self.browser.current_results[0].source_type, "excel")
    
    def test_date_range_filter(self):
        """Test filtering by date range."""
        # Set filter to "Diese Woche"
        self.browser.date_range_var.set("Diese Woche")
        self.browser._load_results()
        
        # Should find 2 recent results (not the 30-day old one)
        self.assertEqual(len(self.browser.current_results), 2)
        for result in self.browser.current_results:
            self.assertGreater(result.created_at, datetime.now() - timedelta(days=7))
    
    def test_exportable_data_filter(self):
        """Test filtering by exportable data presence."""
        # Set filter for exportable data
        self.browser.has_export_var.set(True)
        self.browser._load_results()
        
        # Should find only the Excel result (has table data)
        self.assertEqual(len(self.browser.current_results), 1)
        self.assertTrue(self.browser.current_results[0].has_exportable_data)
    
    def test_clear_filters(self):
        """Test clearing all filters."""
        # Set some filters
        self.browser.analysis_type_var.set("zusammenfassung")
        self.browser.search_var.set("test")
        self.browser.has_export_var.set(True)
        
        # Clear filters
        self.browser._clear_filters()
        
        # Should reset all filters and show all results
        self.assertEqual(self.browser.analysis_type_var.get(), "Alle")
        self.assertEqual(self.browser.search_var.get(), "")
        self.assertFalse(self.browser.has_export_var.get())
        self.assertEqual(len(self.browser.current_results), 3)
    
    def test_selection_handling(self):
        """Test result selection and UI updates."""
        # Simulate selecting first item
        tree_items = self.browser.results_tree.get_children()
        if tree_items:
            self.browser.results_tree.selection_set(tree_items[0])
            self.browser._on_selection_changed(None)
            
            # Should have one selected result
            self.assertEqual(len(self.browser.selected_results), 1)
            
            # Action buttons should be enabled appropriately
            self.assertEqual(str(self.browser.open_button['state']), 'normal')
            self.assertEqual(str(self.browser.export_button['state']), 'normal')
            self.assertEqual(str(self.browser.delete_button['state']), 'normal')
    
    def test_multiple_selection(self):
        """Test multiple result selection."""
        # Simulate selecting multiple items
        tree_items = self.browser.results_tree.get_children()
        if len(tree_items) >= 2:
            self.browser.results_tree.selection_set(tree_items[:2])
            self.browser._on_selection_changed(None)
            
            # Should have two selected results
            self.assertEqual(len(self.browser.selected_results), 2)
            
            # Compare button should be enabled
            self.assertEqual(str(self.browser.compare_button['state']), 'normal')
            # Open button should be disabled (multiple selection)
            self.assertEqual(str(self.browser.open_button['state']), 'disabled')
    
    @patch('tkinter.messagebox.showinfo')
    @patch('tkinter.messagebox.askyesno')
    def test_delete_results(self, mock_askyesno, _mock_showinfo):
        """Test deleting selected results."""
        mock_askyesno.return_value = True
        
        # Select first result
        tree_items = self.browser.results_tree.get_children()
        if tree_items:
            self.browser.results_tree.selection_set(tree_items[0])
            self.browser._on_selection_changed(None)
            
            initial_count = len(self.browser.current_results)
            
            # Delete selected result
            self.browser._delete_selected_results()
            
            # Should have one less result
            self.assertEqual(len(self.browser.current_results), initial_count - 1)
    
    def test_open_result_callback(self):
        """Test opening a result calls the callback."""
        # Select first result
        tree_items = self.browser.results_tree.get_children()
        if tree_items:
            self.browser.results_tree.selection_set(tree_items[0])
            self.browser._on_selection_changed(None)
            
            # Open selected result
            self.browser._open_selected_result()
            
            # Callback should have been called
            self.mock_callback.assert_called_once()
    
    def test_refresh_results(self):
        """Test refreshing the results list."""
        initial_count = len(self.browser.current_results)
        
        # Add a new result directly to manager
        new_result = ProcessedResult(
            content="New test result",
            metadata=ResultMetadata(analysis_type="test")
        )
        self.results_manager.save_result(new_result, "New Result")
        
        # Refresh browser
        self.browser._refresh_results()
        
        # Should show the new result
        self.assertEqual(len(self.browser.current_results), initial_count + 1)
    
    @patch('tkinter.messagebox.showinfo')
    @patch('tkinter.filedialog.askdirectory')
    def test_export_results(self, mock_askdir, _mock_showinfo):
        """Test exporting selected results."""
        mock_askdir.return_value = self.temp_dir
        
        # Select first result
        tree_items = self.browser.results_tree.get_children()
        if tree_items:
            self.browser.results_tree.selection_set(tree_items[0])
            self.browser._on_selection_changed(None)
            
            # Mock the export format dialog
            with patch('results_browser.ExportFormatDialog') as mock_dialog:
                mock_dialog.return_value.result = "json"
                
                # Export selected results
                self.browser._export_selected_results()
                
                # Dialog should have been created
                mock_dialog.assert_called_once()


class TestExportFormatDialog(unittest.TestCase):
    """Test cases for ExportFormatDialog."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()
    
    def tearDown(self):
        """Clean up test environment."""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_dialog_creation(self):
        """Test that dialog creates correctly."""
        # Mock the wait_window method to prevent blocking
        with patch.object(tk.Toplevel, 'wait_window'):
            dialog = ExportFormatDialog(self.root)
            self.assertIsNotNone(dialog.dialog)
            self.assertIsNotNone(dialog.format_var)
    
    def test_ok_button_sets_result(self):
        """Test that OK button sets the result."""
        with patch.object(tk.Toplevel, 'wait_window'):
            dialog = ExportFormatDialog(self.root)
            dialog.format_var.set("txt")
            dialog._ok_clicked()
            self.assertEqual(dialog.result, "txt")
    
    def test_cancel_button_clears_result(self):
        """Test that Cancel button clears the result."""
        with patch.object(tk.Toplevel, 'wait_window'):
            dialog = ExportFormatDialog(self.root)
            dialog._cancel_clicked()
            self.assertIsNone(dialog.result)


class TestComparisonWindow(unittest.TestCase):
    """Test cases for ComparisonWindow."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = f"{self.temp_dir}/test_results.db"
        self.results_dir = f"{self.temp_dir}/test_results"
        
        self.results_manager = ResultsManager(self.db_path, self.results_dir)
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Create test results
        self.result1 = ProcessedResult(
            content="First result content",
            metadata=ResultMetadata(analysis_type="type1")
        )
        self.result2 = ProcessedResult(
            content="Second result content", 
            metadata=ResultMetadata(analysis_type="type2")
        )
        
        self.results_manager.save_result(self.result1, "Result 1")
        self.results_manager.save_result(self.result2, "Result 2")
        
        # Create result summaries
        self.summaries = [
            ResultSummary(
                id=self.result1.id,
                title="Result 1",
                analysis_type="type1",
                source_type="test",
                created_at=datetime.now(),
                has_visualizations=False,
                has_exportable_data=False
            ),
            ResultSummary(
                id=self.result2.id,
                title="Result 2", 
                analysis_type="type2",
                source_type="test",
                created_at=datetime.now(),
                has_visualizations=False,
                has_exportable_data=False
            )
        ]
    
    def tearDown(self):
        """Clean up test environment."""
        try:
            self.root.destroy()
        except:
            pass
        shutil.rmtree(self.temp_dir)
    
    def test_comparison_window_creation(self):
        """Test that comparison window creates correctly."""
        window = ComparisonWindow(self.root, self.summaries, self.results_manager)
        self.assertIsNotNone(window.window)
        self.assertEqual(len(window.results), 2)


class TestStatisticsWindow(unittest.TestCase):
    """Test cases for StatisticsWindow."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = f"{self.temp_dir}/test_results.db"
        self.results_dir = f"{self.temp_dir}/test_results"
        
        self.results_manager = ResultsManager(self.db_path, self.results_dir)
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Create test result
        result = ProcessedResult(
            content="Test content",
            metadata=ResultMetadata(analysis_type="test")
        )
        self.results_manager.save_result(result, "Test Result")
    
    def tearDown(self):
        """Clean up test environment."""
        try:
            self.root.destroy()
        except:
            pass
        shutil.rmtree(self.temp_dir)
    
    def test_statistics_window_creation(self):
        """Test that statistics window creates correctly."""
        window = StatisticsWindow(self.root, self.results_manager)
        self.assertIsNotNone(window.window)
        self.assertIsNotNone(window.stats_text)


class TestResultsBrowserIntegration(unittest.TestCase):
    """Integration tests for ResultsBrowser with real data."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = f"{self.temp_dir}/test_results.db"
        self.results_dir = f"{self.temp_dir}/test_results"
        
        self.results_manager = ResultsManager(self.db_path, self.results_dir)
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Create browser
        self.browser = ResultsBrowser(self.root, self.results_manager)
    
    def tearDown(self):
        """Clean up test environment."""
        try:
            self.root.destroy()
        except:
            pass
        shutil.rmtree(self.temp_dir)
    
    def test_empty_database_handling(self):
        """Test browser behavior with empty database."""
        self.assertEqual(len(self.browser.current_results), 0)
        
        # All action buttons should be disabled
        self.assertEqual(str(self.browser.open_button['state']), 'disabled')
        self.assertEqual(str(self.browser.export_button['state']), 'disabled')
        self.assertEqual(str(self.browser.compare_button['state']), 'disabled')
        self.assertEqual(str(self.browser.delete_button['state']), 'disabled')
    
    def test_filter_options_update(self):
        """Test that filter options update based on available data."""
        # Initially should have default options
        analysis_types = list(self.browser.analysis_type_combo['values'])
        self.assertIn("Alle", analysis_types)
        
        # Add a result with specific type
        result = ProcessedResult(
            content="Test content",
            metadata=ResultMetadata(analysis_type="custom_type")
        )
        self.results_manager.save_result(result, "Custom Result")
        
        # Refresh and check options updated
        self.browser._refresh_results()
        analysis_types = list(self.browser.analysis_type_combo['values'])
        self.assertIn("custom_type", analysis_types)
    
    def test_combined_filters(self):
        """Test using multiple filters together."""
        # Create results with different characteristics
        result1 = ProcessedResult(
            content="Website content with keyword",
            source_info=SourceInfo(type="website"),
            metadata=ResultMetadata(analysis_type="zusammenfassung")
        )
        
        result2 = ProcessedResult(
            content="Excel content with keyword",
            source_info=SourceInfo(type="excel"),
            metadata=ResultMetadata(analysis_type="datenextraktion")
        )
        
        result3 = ProcessedResult(
            content="PDF content without keyword",
            source_info=SourceInfo(type="pdf"),
            metadata=ResultMetadata(analysis_type="zusammenfassung")
        )
        
        self.results_manager.save_result(result1, "Website Result")
        self.results_manager.save_result(result2, "Excel Result")
        self.results_manager.save_result(result3, "PDF Result")
        
        # Apply multiple filters
        self.browser.analysis_type_var.set("zusammenfassung")
        self.browser.search_var.set("Website content")  # More specific search
        self.browser._load_results()
        
        # Should find only the website result (zusammenfassung + "Website content")
        self.assertEqual(len(self.browser.current_results), 1)
        self.assertEqual(self.browser.current_results[0].source_type, "website")


if __name__ == '__main__':
    # Run tests with minimal GUI interaction
    unittest.main(verbosity=2)