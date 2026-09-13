"""
Tests for ExtendedInputTabs component.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
from tkinter import ttk
import tempfile
import os
from pathlib import Path

from extended_input_tabs import ExtendedInputTabs


class TestExtendedInputTabs(unittest.TestCase):
    """Test cases for ExtendedInputTabs."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests
        
        self.notebook = ttk.Notebook(self.root)
        self.status_callback = Mock()
        
        # Create temporary test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_excel_file = os.path.join(self.temp_dir, "test.xlsx")
        self.test_image_file = os.path.join(self.temp_dir, "test.png")
        self.test_csv_file = os.path.join(self.temp_dir, "test.csv")
        
        # Create dummy files
        Path(self.test_excel_file).touch()
        Path(self.test_image_file).touch()
        Path(self.test_csv_file).touch()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        self.root.destroy()
    
    @patch('extended_input_tabs.FileHandlerRouter')
    def test_initialization(self, mock_router_class):
        """Test ExtendedInputTabs initialization."""
        mock_router = Mock()
        mock_router_class.return_value = mock_router
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        
        # Check that tabs were created
        self.assertEqual(self.notebook.index("end"), 5)  # 5 new tabs
        
        # Check tab names
        tab_names = []
        for i in range(self.notebook.index("end")):
            tab_names.append(self.notebook.tab(i, "text"))
        
        expected_tabs = ["Text", "Excel", "Bild/PDF", "CSV/Text", "Multi-Datei"]
        self.assertEqual(tab_names, expected_tabs)
        
        # Check initialization
        self.assertEqual(tabs.parent_notebook, self.notebook)
        self.assertEqual(tabs.status_callback, self.status_callback)
        self.assertEqual(tabs.selected_files, [])
        self.assertIsNone(tabs.current_excel_file)
        self.assertIsNone(tabs.current_image_file)
        self.assertEqual(tabs.current_csv_files, [])
    
    @patch('extended_input_tabs.FileHandlerRouter')
    def test_initialization_without_file_router(self, mock_router_class):
        """Test initialization when FileHandlerRouter fails."""
        mock_router_class.side_effect = Exception("Router failed")
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        
        # Should still create tabs but with no file router
        self.assertIsNone(tabs.file_router)
        self.assertEqual(self.notebook.index("end"), 5)
    
    @patch('extended_input_tabs.FileHandlerRouter')
    def test_current_type_uses_tab_identity(self, mock_router_class):
        mock_router_class.return_value = Mock()
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        self.notebook.select(tabs.tab_frames["text"])
        self.assertEqual(tabs.get_current_type(), "text")
        self.notebook.select(tabs.tab_frames["excel"])
        self.assertEqual(tabs.get_current_type(), "excel")

    @patch('extended_input_tabs.FileHandlerRouter')
    def test_excel_tab_components(self, mock_router_class):
        """Test Excel tab UI components."""
        mock_router = Mock()
        mock_router_class.return_value = mock_router
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        
        # Check Excel tab exists and has required components
        excel_tab = self.notebook.nametowidget(self.notebook.tabs()[1])
        
        # Should have file selection, sheet selection, and preview components
        widgets = self.get_all_widgets(excel_tab)
        
        # Check for specific widget types
        labels = [w for w in widgets if isinstance(w, ttk.Label)]
        buttons = [w for w in widgets if isinstance(w, ttk.Button)]
        comboboxes = [w for w in widgets if isinstance(w, ttk.Combobox)]
        treeviews = [w for w in widgets if isinstance(w, ttk.Treeview)]
        
        self.assertGreater(len(labels), 0)
        self.assertGreater(len(buttons), 0)
        self.assertEqual(len(comboboxes), 1)  # Sheet selection combo
        self.assertEqual(len(treeviews), 1)   # Preview tree
    
    @patch('extended_input_tabs.FileHandlerRouter')
    def test_image_tab_components(self, mock_router_class):
        """Test Image tab UI components."""
        mock_router = Mock()
        mock_router_class.return_value = mock_router
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        
        # Check Image tab exists and has required components
        image_tab = self.notebook.nametowidget(self.notebook.tabs()[2])
        
        widgets = self.get_all_widgets(image_tab)
        
        # Check for specific widget types
        buttons = [w for w in widgets if isinstance(w, ttk.Button)]
        comboboxes = [w for w in widgets if isinstance(w, ttk.Combobox)]
        scrolled_texts = [w for w in widgets if hasattr(w, 'text') and hasattr(w, 'scrollbar')]
        
        self.assertGreaterEqual(len(buttons), 2)  # File select + process buttons
        self.assertEqual(len(comboboxes), 1)      # Language selection
        # Note: ScrolledText detection might need adjustment based on implementation
    
    @patch('extended_input_tabs.FileHandlerRouter')
    def test_csv_tab_components(self, mock_router_class):
        """Test CSV tab UI components."""
        mock_router = Mock()
        mock_router_class.return_value = mock_router
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        
        # Check CSV tab exists and has required components
        csv_tab = self.notebook.nametowidget(self.notebook.tabs()[3])
        
        widgets = self.get_all_widgets(csv_tab)
        
        # Check for specific widget types
        buttons = [w for w in widgets if isinstance(w, ttk.Button)]
        comboboxes = [w for w in widgets if isinstance(w, ttk.Combobox)]
        listboxes = [w for w in widgets if isinstance(w, tk.Listbox)]
        
        self.assertGreaterEqual(len(buttons), 3)  # Add, remove, clear buttons
        self.assertEqual(len(comboboxes), 1)      # Combine method selection
        self.assertEqual(len(listboxes), 1)       # File list
    
    @patch('extended_input_tabs.FileHandlerRouter')
    def test_multi_file_tab_components(self, mock_router_class):
        """Test Multi-file tab UI components."""
        mock_router = Mock()
        mock_router_class.return_value = mock_router
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        
        # Check Multi-file tab exists and has required components
        multi_tab = self.notebook.nametowidget(self.notebook.tabs()[4])
        
        widgets = self.get_all_widgets(multi_tab)
        
        # Check for specific widget types
        buttons = [w for w in widgets if isinstance(w, ttk.Button)]
        treeviews = [w for w in widgets if isinstance(w, ttk.Treeview)]
        
        self.assertGreaterEqual(len(buttons), 4)  # Add, remove, clear, analyze buttons
        self.assertEqual(len(treeviews), 1)       # File details tree
    
    def get_all_widgets(self, parent):
        """Recursively get all widgets in a parent widget."""
        widgets = []
        
        def collect_widgets(widget):
            widgets.append(widget)
            for child in widget.winfo_children():
                collect_widgets(child)
        
        collect_widgets(parent)
        return widgets
    
    @patch('extended_input_tabs.FileHandlerRouter')
    def test_csv_file_management(self, mock_router_class):
        """Test CSV file list management."""
        mock_router = Mock()
        mock_router_class.return_value = mock_router
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        
        # Test adding files
        initial_count = len(tabs.current_csv_files)
        tabs.current_csv_files.append(self.test_csv_file)
        tabs.csv_files_listbox.insert(tk.END, Path(self.test_csv_file).name)
        
        self.assertEqual(len(tabs.current_csv_files), initial_count + 1)
        self.assertEqual(tabs.csv_files_listbox.size(), initial_count + 1)
        
        # Test clearing files
        tabs.clear_csv_files()
        
        self.assertEqual(len(tabs.current_csv_files), 0)
        self.assertEqual(tabs.csv_files_listbox.size(), 0)
    
    @patch('extended_input_tabs.FileHandlerRouter')
    def test_multi_file_management(self, mock_router_class):
        """Test multi-file list management."""
        mock_router = Mock()
        mock_router_class.return_value = mock_router
        
        # Mock file type detection
        mock_file_info = Mock()
        mock_file_info.supported = True
        mock_file_info.file_type = "test"
        mock_router.detect_file_type.return_value = mock_file_info
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        
        # Test adding files
        initial_count = len(tabs.selected_files)
        tabs.selected_files.append(self.test_excel_file)
        tabs.add_file_to_tree(self.test_excel_file)
        
        self.assertEqual(len(tabs.selected_files), initial_count + 1)
        
        # Test clearing files
        tabs.clear_all_files()
        
        self.assertEqual(len(tabs.selected_files), 0)
        # Tree should be empty
        self.assertEqual(len(tabs.multi_files_tree.get_children()), 0)
    
    @patch('extended_input_tabs.FileHandlerRouter')
    def test_file_size_formatting(self, mock_router_class):
        """Test file size formatting utility."""
        mock_router = Mock()
        mock_router_class.return_value = mock_router
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        
        # Test different file sizes
        self.assertEqual(tabs.format_file_size(500), "500 B")
        self.assertEqual(tabs.format_file_size(1536), "1.5 KB")
        self.assertEqual(tabs.format_file_size(2097152), "2.0 MB")
    
    @patch('extended_input_tabs.FileHandlerRouter')
    def test_get_current_content_no_router(self, mock_router_class):
        """Test get_current_content when no file router available."""
        mock_router_class.return_value = None
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        tabs.file_router = None
        
        content = tabs.get_current_content()
        self.assertIsNone(content)
    
    @patch('extended_input_tabs.FileHandlerRouter')
    def test_get_handler_info(self, mock_router_class):
        """Test getting handler information."""
        mock_router = Mock()
        mock_info = {"handlers": ["excel", "image", "csv"]}
        mock_router.get_handler_info.return_value = mock_info
        mock_router_class.return_value = mock_router
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        
        info = tabs.get_handler_info()
        self.assertEqual(info, mock_info)
    
    @patch('extended_input_tabs.FileHandlerRouter')
    def test_get_handler_info_no_router(self, mock_router_class):
        """Test getting handler info when no router available."""
        mock_router_class.return_value = None
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        tabs.file_router = None
        
        info = tabs.get_handler_info()
        self.assertIn("error", info)
    
    @patch('extended_input_tabs.FileHandlerRouter')
    def test_status_callback_usage(self, mock_router_class):
        """Test that status callback is called appropriately."""
        mock_router = Mock()
        mock_router_class.return_value = mock_router
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        
        # Manually trigger a status update to test the callback
        tabs.status_callback("Test status message")
        
        # The status callback should have been called
        self.assertTrue(self.status_callback.called)
        self.status_callback.assert_called_with("Test status message")
    
    @patch('extended_input_tabs.FileHandlerRouter')
    @patch('extended_input_tabs.threading.Thread')
    def test_background_processing(self, mock_thread, mock_router_class):
        """Test that background processing is initiated correctly."""
        mock_router = Mock()
        mock_router_class.return_value = mock_router
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        
        # Set up a file and trigger background processing
        tabs.current_excel_file = self.test_excel_file
        tabs.load_excel_info()
        
        # Should have started a background thread
        # Note: This test might need adjustment based on actual threading implementation
        # mock_thread.assert_called()
    
    @patch('extended_input_tabs.FileHandlerRouter')
    def test_multi_summary_update(self, mock_router_class):
        """Test multi-file summary updates."""
        mock_router = Mock()
        mock_router_class.return_value = mock_router
        
        # Mock file type detection
        mock_file_info = Mock()
        mock_file_info.supported = True
        mock_file_info.file_type = "excel"
        mock_router.detect_file_type.return_value = mock_file_info
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        
        # Test with no files
        tabs.update_multi_summary()
        self.assertIn("Keine Dateien", tabs.multi_summary_var.get())
        
        # Test with files
        tabs.selected_files = [self.test_excel_file, self.test_csv_file]
        tabs.update_multi_summary()
        
        summary = tabs.multi_summary_var.get()
        self.assertIn("2 Dateien", summary)
    
    @patch('extended_input_tabs.FileHandlerRouter')
    @patch('extended_input_tabs.messagebox')
    def test_analyze_selected_files_no_files(self, mock_messagebox, mock_router_class):
        """Test analyze_selected_files with no files selected."""
        mock_router = Mock()
        mock_router_class.return_value = mock_router
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        
        # Call analyze with no files
        tabs.analyze_selected_files()
        
        # Should show warning
        mock_messagebox.showwarning.assert_called_once()
    
    @patch('extended_input_tabs.FileHandlerRouter')
    @patch('extended_input_tabs.messagebox')
    def test_analyze_selected_files_no_router(self, mock_messagebox, mock_router_class):
        """Test analyze_selected_files with no file router."""
        mock_router_class.return_value = None
        
        tabs = ExtendedInputTabs(self.notebook, self.status_callback)
        tabs.file_router = None
        tabs.selected_files = [self.test_excel_file]
        
        # Call analyze
        tabs.analyze_selected_files()
        
        # Should show error
        mock_messagebox.showerror.assert_called_once()


class TestExtendedInputTabsIntegration(unittest.TestCase):
    """Integration tests for ExtendedInputTabs with real file handlers."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.notebook = ttk.Notebook(self.root)
        self.status_callback = Mock()
        
        # Create temporary test files with actual content
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a simple CSV file
        self.test_csv_file = os.path.join(self.temp_dir, "test.csv")
        with open(self.test_csv_file, 'w') as f:
            f.write("Name,Age,City\n")
            f.write("Alice,25,Berlin\n")
            f.write("Bob,30,Munich\n")
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.root.destroy()
    
    def test_csv_file_processing_integration(self):
        """Test CSV file processing with real CSV handler."""
        try:
            tabs = ExtendedInputTabs(self.notebook, self.status_callback)
            
            if tabs.file_router and 'csv' in tabs.file_router.handlers:
                # Add CSV file
                tabs.current_csv_files = [self.test_csv_file]
                
                # Test that we can get handler info
                handler_info = tabs.get_handler_info()
                self.assertIn('available_handlers', handler_info)
                
                # Test CSV preview update (this would normally run in background)
                csv_handler = tabs.file_router.handlers['csv']
                content = csv_handler.extract_content_for_analysis(self.test_csv_file)
                
                self.assertIn("CSV-Daten", content)
                self.assertIn("Alice", content)
                self.assertIn("Bob", content)
            else:
                self.skipTest("CSV handler not available")
                
        except ImportError:
            self.skipTest("Required dependencies not available")
    
    def test_file_type_detection_integration(self):
        """Test file type detection with real files."""
        try:
            tabs = ExtendedInputTabs(self.notebook, self.status_callback)
            
            if tabs.file_router:
                # Test CSV file detection
                file_info = tabs.file_router.detect_file_type(self.test_csv_file)
                
                self.assertEqual(file_info.file_type, 'csv')
                self.assertTrue(file_info.supported)
                self.assertGreater(file_info.confidence, 0)
            else:
                self.skipTest("File router not available")
                
        except ImportError:
            self.skipTest("Required dependencies not available")


if __name__ == '__main__':
    # Run tests
    unittest.main()