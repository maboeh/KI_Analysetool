"""
Tests for Excel Export UI Integration

This module contains tests for the Excel export UI components,
including dialogs, buttons, and integration functionality.
"""

import unittest
import tempfile
import os
import tkinter as tk
from unittest.mock import patch, MagicMock, call
from datetime import datetime

from excel_export_ui import (
    ExcelExportDialog, ExcelExportButton, ExportOptions,
    integrate_excel_export_with_action_buttons, create_quick_export_function
)
from excel_exporter import ExcelExporter
from data_models import (
    ProcessedResult, StructuredData, DataTable, NamedEntity,
    EntityType, ResultMetadata, SourceInfo
)


class TestExcelExportDialog(unittest.TestCase):
    """Test cases for ExcelExportDialog"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window
        
        # Create sample data
        self.sample_table = DataTable(
            headers=['Name', 'Value'],
            rows=[['Test1', '100'], ['Test2', '200']],
            title='Test Table'
        )
        
        self.sample_entity = NamedEntity(
            text='Test Entity',
            entity_type=EntityType.PERSON,
            confidence=0.9
        )
        
        self.sample_result = ProcessedResult(
            content='Test analysis result with structured data',
            source_info=SourceInfo(type='test', file_name='test.txt'),
            extracted_data=StructuredData(
                tables=[self.sample_table],
                entities=[self.sample_entity]
            ),
            metadata=ResultMetadata(analysis_type='Test Analysis')
        )
        
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.root.destroy()
        
        # Clean up temporary files
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def test_dialog_initialization(self):
        """Test dialog initialization with valid data"""
        dialog = ExcelExportDialog(self.root, self.sample_result)
        
        self.assertIsInstance(dialog, ExcelExportDialog)
        self.assertEqual(dialog.result, self.sample_result)
        self.assertIsInstance(dialog.exporter, ExcelExporter)
        self.assertIsInstance(dialog.export_options, ExportOptions)
        
        dialog.destroy()
    
    def test_dialog_with_empty_result(self):
        """Test dialog with result containing no structured data"""
        empty_result = ProcessedResult(
            content='Just text, no structured data',
            metadata=ResultMetadata(analysis_type='Simple Analysis')
        )
        
        dialog = ExcelExportDialog(self.root, empty_result)
        
        # Dialog should still initialize but with warnings
        self.assertIsInstance(dialog, ExcelExportDialog)
        
        dialog.destroy()
    
    @patch('excel_export_ui.messagebox.showerror')
    @patch('excel_export_ui.messagebox.showinfo')
    def test_export_functionality(self, mock_showinfo, mock_showerror):
        """Test the export functionality"""
        dialog = ExcelExportDialog(self.root, self.sample_result)
        
        # Set a test file path
        test_file = os.path.join(self.temp_dir, 'test_export.xlsx')
        dialog.file_path_var.set(test_file)
        
        # Mock the export method to return success
        with patch.object(dialog.exporter, 'export_to_excel', return_value=True):
            dialog._export_data()
        
        # Verify success message was shown
        mock_showinfo.assert_called_once()
        self.assertTrue(dialog.export_successful)
        
        dialog.destroy()
    
    @patch('excel_export_ui.messagebox.showerror')
    def test_export_failure(self, mock_showerror):
        """Test export failure handling"""
        dialog = ExcelExportDialog(self.root, self.sample_result)
        
        # Set a test file path
        test_file = os.path.join(self.temp_dir, 'test_export.xlsx')
        dialog.file_path_var.set(test_file)
        
        # Mock the export method to return failure
        with patch.object(dialog.exporter, 'export_to_excel', return_value=False):
            dialog._export_data()
        
        # Verify error message was shown
        mock_showerror.assert_called_once()
        self.assertFalse(dialog.export_successful)
        
        dialog.destroy()
    
    def test_template_selection(self):
        """Test template selection functionality"""
        dialog = ExcelExportDialog(self.root, self.sample_result)
        
        # Test template change
        dialog.template_var.set('tables_only')
        dialog._on_template_changed()
        
        # Verify template description is updated
        self.assertIn('Tabellendaten', dialog.template_desc_label.cget('text'))
        
        dialog.destroy()
    
    def test_filename_generation(self):
        """Test automatic filename generation"""
        dialog = ExcelExportDialog(self.root, self.sample_result)
        
        # Test auto filename generation
        dialog.auto_filename_var.set(True)
        dialog._generate_filename()
        
        filename = dialog.file_path_var.get()
        self.assertTrue(filename.endswith('.xlsx'))
        self.assertIn('analyse_ergebnis', filename.lower())
        
        dialog.destroy()
    
    def test_preview_update(self):
        """Test preview functionality"""
        dialog = ExcelExportDialog(self.root, self.sample_result)
        
        # Update preview
        dialog._update_preview()
        
        # Check that preview text is populated
        preview_content = dialog.preview_text.get(1.0, tk.END)
        self.assertIn('Vorlage:', preview_content)
        self.assertIn('Arbeitsblätter', preview_content)
        
        dialog.destroy()
    
    @patch('excel_export_ui.filedialog.asksaveasfilename')
    def test_file_browser(self, mock_filedialog):
        """Test file browser functionality"""
        dialog = ExcelExportDialog(self.root, self.sample_result)
        
        # Mock file dialog to return a path
        test_path = os.path.join(self.temp_dir, 'selected_file.xlsx')
        mock_filedialog.return_value = test_path
        
        dialog._browse_file()
        
        # Verify path was set
        self.assertEqual(dialog.file_path_var.get(), test_path)
        self.assertFalse(dialog.auto_filename_var.get())
        
        dialog.destroy()


class TestExcelExportButton(unittest.TestCase):
    """Test cases for ExcelExportButton"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.sample_result = ProcessedResult(
            content='Test content',
            extracted_data=StructuredData(
                tables=[DataTable(headers=['A'], rows=[['1']])]
            ),
            metadata=ResultMetadata(analysis_type='Test')
        )
        
        self.result_provider = lambda: self.sample_result
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.root.destroy()
    
    def test_button_initialization(self):
        """Test button initialization"""
        button = ExcelExportButton(self.root, self.result_provider)
        
        self.assertIsInstance(button, ExcelExportButton)
        self.assertEqual(button.result_provider, self.result_provider)
        self.assertIsInstance(button.exporter, ExcelExporter)
        
        button.destroy()
    
    def test_button_state_with_data(self):
        """Test button state when data is available"""
        button = ExcelExportButton(self.root, self.result_provider)
        
        # Button should be enabled with exportable data
        self.assertEqual(str(button.cget('state')), 'normal')
        self.assertIn('Excel Export', button.cget('text'))
        
        button.destroy()
    
    def test_button_state_without_data(self):
        """Test button state when no data is available"""
        empty_provider = lambda: None
        button = ExcelExportButton(self.root, empty_provider)
        
        # Button should be disabled without data
        self.assertEqual(str(button.cget('state')), 'disabled')
        
        button.destroy()
    
    def test_button_state_with_text_only(self):
        """Test button state with text-only result"""
        text_only_result = ProcessedResult(
            content='Just text content',
            metadata=ResultMetadata(analysis_type='Text Analysis')
        )
        text_provider = lambda: text_only_result
        
        button = ExcelExportButton(self.root, text_provider)
        
        # Button should be enabled but with different text
        self.assertEqual(str(button.cget('state')), 'normal')
        self.assertIn('Zusammenfassung', button.cget('text'))
        
        button.destroy()
    
    @patch('excel_export_ui.ExcelExportDialog')
    def test_button_click_with_data(self, mock_dialog_class):
        """Test button click behavior with valid data"""
        button = ExcelExportButton(self.root, self.result_provider)
        
        # Mock dialog
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog
        
        # Simulate button click
        with patch.object(button, 'wait_window'):
            button._on_export_click()
        
        # Verify dialog was created and shown
        mock_dialog_class.assert_called_once()
        
        button.destroy()
    
    @patch('excel_export_ui.messagebox.showwarning')
    def test_button_click_without_data(self, mock_warning):
        """Test button click behavior without data"""
        empty_provider = lambda: None
        button = ExcelExportButton(self.root, empty_provider)
        
        # Simulate button click
        button._on_export_click()
        
        # Verify warning was shown
        mock_warning.assert_called_once()
        
        button.destroy()


class TestActionButtonsIntegration(unittest.TestCase):
    """Test cases for action buttons integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Mock ActionButtonsFrame
        self.mock_action_frame = MagicMock()
        self.mock_action_frame.winfo_toplevel.return_value = self.root
        self.mock_action_frame.wait_window = MagicMock()
        
        self.sample_result = ProcessedResult(
            content='Test content',
            extracted_data=StructuredData(
                tables=[DataTable(headers=['A'], rows=[['1']])]
            ),
            metadata=ResultMetadata(analysis_type='Test')
        )
        
        self.result_provider = lambda: self.sample_result
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.root.destroy()
    
    def test_integration_function(self):
        """Test integration with action buttons frame"""
        integrate_excel_export_with_action_buttons(
            self.mock_action_frame, 
            self.result_provider
        )
        
        # Verify that add_custom_action was called
        self.mock_action_frame.add_custom_action.assert_called_once()
        
        # Get the action that was added
        call_args = self.mock_action_frame.add_custom_action.call_args[0][0]
        self.assertEqual(call_args.label, "Excel Export")
        self.assertIsNotNone(call_args.callback)
    
    @patch('excel_export_ui.ExcelExportDialog')
    def test_integrated_export_action(self, mock_dialog_class):
        """Test the integrated export action execution"""
        integrate_excel_export_with_action_buttons(
            self.mock_action_frame,
            self.result_provider
        )
        
        # Get the callback function
        call_args = self.mock_action_frame.add_custom_action.call_args[0][0]
        callback = call_args.callback
        
        # Mock dialog
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog
        
        # Execute the callback
        callback()
        
        # Verify dialog was created
        mock_dialog_class.assert_called_once()


class TestQuickExportFunction(unittest.TestCase):
    """Test cases for quick export function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.sample_result = ProcessedResult(
            content='Test content',
            extracted_data=StructuredData(
                tables=[DataTable(headers=['A'], rows=[['1']])]
            ),
            metadata=ResultMetadata(analysis_type='Test')
        )
        
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.root.destroy()
        
        # Clean up temporary files
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    @patch('excel_export_ui.filedialog.asksaveasfilename')
    @patch('excel_export_ui.messagebox.showinfo')
    def test_quick_export_success(self, mock_showinfo, mock_filedialog):
        """Test successful quick export"""
        test_file = os.path.join(self.temp_dir, 'quick_export.xlsx')
        mock_filedialog.return_value = test_file
        
        # Mock the exporter
        with patch('excel_export_ui.ExcelExporter') as mock_exporter_class:
            mock_exporter = MagicMock()
            mock_exporter.export_to_excel.return_value = True
            mock_exporter_class.return_value = mock_exporter
            
            result = create_quick_export_function(self.sample_result, self.root)
            
            self.assertTrue(result)
            mock_showinfo.assert_called_once()
            mock_exporter.export_to_excel.assert_called_once()
    
    @patch('excel_export_ui.filedialog.asksaveasfilename')
    def test_quick_export_cancelled(self, mock_filedialog):
        """Test quick export when user cancels file dialog"""
        mock_filedialog.return_value = ''  # User cancelled
        
        result = create_quick_export_function(self.sample_result, self.root)
        
        self.assertFalse(result)
    
    @patch('excel_export_ui.filedialog.asksaveasfilename')
    @patch('excel_export_ui.messagebox.showerror')
    def test_quick_export_failure(self, mock_showerror, mock_filedialog):
        """Test quick export failure"""
        test_file = os.path.join(self.temp_dir, 'quick_export.xlsx')
        mock_filedialog.return_value = test_file
        
        # Mock the exporter to fail
        with patch('excel_export_ui.ExcelExporter') as mock_exporter_class:
            mock_exporter = MagicMock()
            mock_exporter.export_to_excel.return_value = False
            mock_exporter_class.return_value = mock_exporter
            
            result = create_quick_export_function(self.sample_result, self.root)
            
            self.assertFalse(result)
            mock_showerror.assert_called_once()


class TestExportOptions(unittest.TestCase):
    """Test cases for ExportOptions dataclass"""
    
    def test_default_options(self):
        """Test default export options"""
        options = ExportOptions()
        
        self.assertEqual(options.template_name, 'complete')
        self.assertEqual(options.file_path, '')
        self.assertTrue(options.include_preview)
        self.assertFalse(options.auto_open)
        self.assertFalse(options.custom_filename)
    
    def test_custom_options(self):
        """Test custom export options"""
        options = ExportOptions(
            template_name='tables_only',
            file_path='/test/path.xlsx',
            include_preview=False,
            auto_open=True,
            custom_filename=True
        )
        
        self.assertEqual(options.template_name, 'tables_only')
        self.assertEqual(options.file_path, '/test/path.xlsx')
        self.assertFalse(options.include_preview)
        self.assertTrue(options.auto_open)
        self.assertTrue(options.custom_filename)


if __name__ == '__main__':
    # Run tests with minimal GUI interaction
    unittest.main(verbosity=2)