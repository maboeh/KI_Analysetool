"""
Final integration tests for the complete enhanced GUI system.

This module tests the complete integration of all enhanced components
with the existing GUI system, ensuring backward compatibility and
proper functionality of all new features.
"""

import unittest
import tempfile
import os
import shutil
import tkinter as tk
from tkinter import ttk
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime

# Import components to test
try:
    from enhanced_gui_integration_final import EnhancedGui
    ENHANCED_GUI_AVAILABLE = True
except ImportError as e:
    ENHANCED_GUI_AVAILABLE = False
    IMPORT_ERROR = str(e)

from Gui import Gui as BaseGui
from analysis import AnalysisOutcome
from data_models import ProcessedResult, StructuredData, ResultMetadata


class TestFinalGUIIntegration(unittest.TestCase):
    """Test complete GUI integration with enhanced features."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test tkinter window
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        self.onboarding_patcher = patch.object(EnhancedGui, '_maybe_show_onboarding')
        self.onboarding_patcher.start()
        
    def tearDown(self):
        """Clean up test environment."""
        self.onboarding_patcher.stop()
        try:
            self.root.destroy()
        except:
            pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    @unittest.skipUnless(ENHANCED_GUI_AVAILABLE, f"Enhanced GUI not available: {IMPORT_ERROR if not ENHANCED_GUI_AVAILABLE else ''}")
    def test_enhanced_gui_initialization(self):
        """Test that enhanced GUI initializes properly."""
        with patch('config.check_api_key_exists', return_value=True):
            gui = EnhancedGui(self.root)
            
            # Verify enhanced components are initialized
            self.assertIsNotNone(gui.results_processor)
            self.assertIsNotNone(gui.results_manager)
            self.assertIsNotNone(gui.file_router)
            
            # Verify enhanced UI components exist
            self.assertTrue(hasattr(gui, 'enhanced_input_tabs'))
            self.assertTrue(hasattr(gui, 'results_display'))
            self.assertTrue(hasattr(gui, 'action_buttons'))
            self.assertTrue(hasattr(gui, 'visualization_panel'))
            self.assertIsInstance(gui.content_frame, ttk.PanedWindow)
            self.assertLessEqual(self.root.minsize()[0], 800)
            self.assertEqual(gui.analysis_button.cget("text"), "Analyse starten")
            
    def test_small_screen_uses_vertical_layout(self):
        with patch('Gui.check_api_key_exists', return_value=True):
            with patch.object(self.root, 'winfo_screenwidth', return_value=1024):
                gui = BaseGui(self.root)
        self.assertEqual(gui.layout_orientation, tk.VERTICAL)
        self.assertIsInstance(gui.content_frame, ttk.PanedWindow)

    def test_base_gui_backward_compatibility(self):
        """Test that base GUI still works without enhanced features."""
        with patch('config.check_api_key_exists', return_value=True):
            gui = BaseGui(self.root)
            
            # Verify basic components exist
            self.assertTrue(hasattr(gui, 'input_tabs'))
            self.assertTrue(hasattr(gui, 'output_text'))
            self.assertTrue(hasattr(gui, 'question_text'))
            
            # Verify basic methods work
            self.assertTrue(hasattr(gui, 'send_question'))
            self.assertTrue(hasattr(gui, 'save_note'))
            
    @unittest.skipUnless(ENHANCED_GUI_AVAILABLE, "Enhanced GUI not available")
    @patch('config.check_api_key_exists', return_value=True)
    @patch('enhanced_gui_integration_final.analyze_text')
    def test_enhanced_analysis_workflow(self, mock_analysis, _mock_key):
        """Test complete enhanced analysis workflow."""
        # Mock AI analysis
        mock_analysis.return_value = AnalysisOutcome(content="Enhanced analysis result with data")
        
        gui = EnhancedGui(self.root)
        
        # Simulate analysis request
        test_content = "Test content for analysis"
        test_source = "test_source.txt"
        
        # Test enhanced analysis processing
        gui._on_enhanced_analysis_requested(test_content, test_source, "test_analysis")
        
        # Wait for background processing (in real app, this would be threaded)
        gui.processing_thread.join(timeout=5)
        
        # Verify analysis was called
        mock_analysis.assert_called()
        
    @unittest.skipUnless(ENHANCED_GUI_AVAILABLE, "Enhanced GUI not available")
    @patch('config.check_api_key_exists', return_value=True)
    def test_results_display_integration(self, _mock_key):
        """Test results display integration."""
        gui = EnhancedGui(self.root)
        gui.auto_save_enabled = False
        
        # Create mock result
        mock_result = ProcessedResult(
            id="test_id",
            content="Test result content",
            source_info=None,
            extracted_data=StructuredData(
                tables=[], entities=[], numeric_values=[],
                temporal_data=[], relationships=[]
            ),
            visualizations=[],
            follow_up_actions=[],
            metadata=ResultMetadata(analysis_type="test"),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Test result display
        gui._display_enhanced_result(mock_result)
        
        # Verify result is stored
        self.assertEqual(gui.current_result, mock_result)
        
    @unittest.skipUnless(ENHANCED_GUI_AVAILABLE, "Enhanced GUI not available")
    @patch('config.check_api_key_exists', return_value=True)
    def test_file_handling_integration(self, _mock_key):
        """Test file handling integration."""
        gui = EnhancedGui(self.root)
        
        # Create test Excel file
        test_data = {'Name': ['Test'], 'Value': [123]}
        excel_file = os.path.join(self.temp_dir, 'test.xlsx')
        pd.DataFrame(test_data).to_excel(excel_file, index=False)
        
        # Test file selection callback
        gui._on_file_selected([excel_file], "excel")
        
        # Verify status was updated
        self.assertIn("ausgewählt", gui.status_var.get())
        
    @unittest.skipUnless(ENHANCED_GUI_AVAILABLE, "Enhanced GUI not available")
    @patch('config.check_api_key_exists', return_value=True)
    def test_action_buttons_integration(self, _mock_key):
        """Test action buttons integration."""
        gui = EnhancedGui(self.root)
        
        # Test action request
        gui._on_action_requested("summarize")
        
        # Should handle gracefully even without current result
        # (In real usage, there would be a current result)
        
    @unittest.skipUnless(ENHANCED_GUI_AVAILABLE, "Enhanced GUI not available")
    @patch('config.check_api_key_exists', return_value=True)
    def test_menu_integration(self, _mock_key):
        """Test enhanced menu integration."""
        gui = EnhancedGui(self.root)
        
        # Verify enhanced menu exists
        self.assertTrue(hasattr(gui, 'enhanced_menu'))
        
        # Test menu actions
        gui._show_results_manager()
        gui._show_export_dialog()
        gui._show_visualization_dialog()
        
        # Should not raise exceptions
        
    @unittest.skipUnless(ENHANCED_GUI_AVAILABLE, "Enhanced GUI not available")
    @patch('config.check_api_key_exists', return_value=True)
    def test_progress_indicator_integration(self, _mock_key):
        """Test progress indicator integration."""
        gui = EnhancedGui(self.root)
        
        # Verify progress indicator exists
        self.assertTrue(hasattr(gui, 'progress_indicator'))
        
        # Test progress operations
        gui.progress_indicator.start("Test operation")
        self.assertTrue(gui.progress_indicator.is_visible)
        gui.progress_indicator.stop()
        self.assertFalse(gui.progress_indicator.is_visible)
        
    @unittest.skipUnless(ENHANCED_GUI_AVAILABLE, "Enhanced GUI not available")
    @patch('config.check_api_key_exists', return_value=True)
    def test_error_handling_integration(self, _mock_key):
        """Test error handling integration."""
        gui = EnhancedGui(self.root)
        
        # Test error display
        with patch('tkinter.messagebox.showerror') as mock_error:
            gui._show_error("Test error message")
            mock_error.assert_called_with("Fehler", "Test error message")
            
    @unittest.skipUnless(ENHANCED_GUI_AVAILABLE, "Enhanced GUI not available")
    @patch('config.check_api_key_exists', return_value=True)
    def test_backward_compatibility_methods(self, _mock_key):
        """Test that enhanced GUI maintains backward compatibility."""
        gui = EnhancedGui(self.root)
        
        # Test that original methods still exist and work
        self.assertTrue(hasattr(gui, 'send_question'))
        self.assertTrue(hasattr(gui, 'save_note'))
        self.assertTrue(hasattr(gui, 'export_notes_as_pdf'))
        self.assertTrue(hasattr(gui, 'copy_notes_as_text'))
        
        # Test that original attributes exist
        self.assertTrue(hasattr(gui, 'output_text'))
        self.assertTrue(hasattr(gui, 'question_text'))
        self.assertTrue(hasattr(gui, 'status_var'))
        
    def test_main_initialization(self):
        """Test main application initialization."""
        # Test dependency checking
        from main import check_dependencies, setup_directories
        
        # Should not raise exceptions
        setup_directories()
        
        # Dependency check should return boolean
        result = check_dependencies()
        self.assertIsInstance(result, bool)
        
    def test_gui_factory_function(self):
        """Test GUI factory function."""
        if ENHANCED_GUI_AVAILABLE:
            with patch('config.check_api_key_exists', return_value=True):
                from enhanced_gui_integration_final import create_enhanced_gui
                
                gui = create_enhanced_gui(self.root)
                self.assertIsInstance(gui, EnhancedGui)
            
    def test_settings_dialog(self):
        """Test settings dialog functionality."""
        if ENHANCED_GUI_AVAILABLE:
            with patch('config.check_api_key_exists', return_value=True):
                gui = EnhancedGui(self.root)
                
                # Test settings dialog creation
                before = set(self.root.winfo_children())
                gui._show_settings_dialog()
                created = set(self.root.winfo_children()) - before
                self.assertTrue(any(isinstance(widget, tk.Toplevel) for widget in created))


class TestGUIComponentIntegration(unittest.TestCase):
    """Test integration between different GUI components."""
    
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
            
    @unittest.skipUnless(ENHANCED_GUI_AVAILABLE, "Enhanced GUI not available")
    @patch('config.check_api_key_exists', return_value=True)
    def test_tab_switching_integration(self, _mock_key):
        """Test switching between different result tabs."""
        gui = EnhancedGui(self.root)
        
        # Test switching to different tabs
        if hasattr(gui, 'result_notebook'):
            # Switch to visualization tab
            gui.result_notebook.select(gui.viz_frame)
            self.assertEqual(gui.result_notebook.select(), str(gui.viz_frame))
            
            # Switch to export tab
            gui.result_notebook.select(gui.export_frame)
            self.assertEqual(gui.result_notebook.select(), str(gui.export_frame))
            
            # Switch to browser tab
            gui.result_notebook.select(gui.browser_frame)
            self.assertEqual(gui.result_notebook.select(), str(gui.browser_frame))
            
    @unittest.skipUnless(ENHANCED_GUI_AVAILABLE, "Enhanced GUI not available")
    @patch('config.check_api_key_exists', return_value=True)
    def test_component_communication(self, _mock_key):
        """Test communication between different GUI components."""
        gui = EnhancedGui(self.root)
        
        # Test that components can communicate through the main GUI
        if hasattr(gui, 'results_display') and hasattr(gui, 'action_buttons'):
            # Components should be able to trigger actions through callbacks
            self.assertTrue(callable(gui._on_action_requested))
            self.assertTrue(callable(gui._on_follow_up_action))


if __name__ == '__main__':
    # Run integration tests
    unittest.main(verbosity=2)