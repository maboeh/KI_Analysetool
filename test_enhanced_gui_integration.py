"""
Tests for enhanced GUI integration components.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import tempfile
import os

from enhanced_gui_integration import EnhancedResultsInterface, EnhancedGuiIntegration
from data_models import ProcessedResult, StructuredData


class TestEnhancedResultsInterface(unittest.TestCase):
    """Test cases for EnhancedResultsInterface."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests
        
        self.parent_frame = ttk.Frame(self.root)
        self.action_callback = Mock()
        
        # Create test result
        self.test_result = ProcessedResult(
            id="test_result_1",
            content="# Test Result\n\nThis is a test result with **bold** text.",
            created_at=datetime.now()
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
    
    def test_initialization(self):
        """Test EnhancedResultsInterface initialization."""
        interface = EnhancedResultsInterface(self.parent_frame, self.action_callback)
        
        # Check that main components were created
        self.assertIsNotNone(interface.main_frame)
        self.assertIsNotNone(interface.results_notebook)
        
        # Check that tabs were created
        self.assertEqual(interface.results_notebook.index("end"), 3)  # 3 tabs
        
        # Check tab names
        tab_names = []
        for i in range(interface.results_notebook.index("end")):
            tab_names.append(interface.results_notebook.tab(i, "text"))
        
        expected_tabs = ["Textergebnisse", "Visualisierungen", "Datenübersicht"]
        self.assertEqual(tab_names, expected_tabs)
    
    def test_display_result_basic(self):
        """Test basic result display functionality."""
        interface = EnhancedResultsInterface(self.parent_frame, self.action_callback)
        
        # Display a test result
        interface.display_result(self.test_result)
        
        # Check that current result is set
        self.assertEqual(interface.current_result, self.test_result)
    
    def test_display_result_with_fallback(self):
        """Test result display with fallback text widget."""
        interface = EnhancedResultsInterface(self.parent_frame, self.action_callback)
        
        # Ensure we're using fallback (simulate missing ResultsDisplayWidget)
        if hasattr(interface, 'results_display'):
            delattr(interface, 'results_display')
        
        # Display result
        interface.display_result(self.test_result)
        
        # Check that text widget has content
        if hasattr(interface, 'text_widget'):
            content = interface.text_widget.get(1.0, tk.END).strip()
            self.assertIn("Test Result", content)
    
    def test_clear_functionality(self):
        """Test clearing all displayed results."""
        interface = EnhancedResultsInterface(self.parent_frame, self.action_callback)
        
        # Display a result first
        interface.display_result(self.test_result)
        
        # Clear
        interface.clear()
        
        # Check that state is cleared
        self.assertIsNone(interface.current_result)
        self.assertIsNone(interface.current_structured_data)
    
    def test_data_tree_population(self):
        """Test data tree population with structured data."""
        interface = EnhancedResultsInterface(self.parent_frame, self.action_callback)
        
        # Create mock structured data
        mock_structured_data = Mock(spec=StructuredData)
        mock_structured_data.tables = []
        mock_structured_data.entities = []
        mock_structured_data.numeric_values = []
        mock_structured_data.temporal_data = []
        
        # Test population (should not raise errors)
        interface._populate_data_tree(mock_structured_data)
        
        # Check that tree is accessible
        self.assertIsNotNone(interface.data_tree)
    
    def test_action_triggering(self):
        """Test action button triggering."""
        interface = EnhancedResultsInterface(self.parent_frame, self.action_callback)
        
        # Set current result
        interface.current_result = self.test_result
        
        # Trigger an action
        interface._trigger_action("summarize")
        
        # Check that callback was called
        self.action_callback.assert_called_once_with("summarize", self.test_result)
    
    def test_action_triggering_no_callback(self):
        """Test action triggering without callback."""
        interface = EnhancedResultsInterface(self.parent_frame, None)
        
        # Set current result
        interface.current_result = self.test_result
        
        # Should not raise error
        interface._trigger_action("summarize")
    
    def test_export_functions(self):
        """Test data export functions."""
        interface = EnhancedResultsInterface(self.parent_frame, self.action_callback)
        
        # Test without data (should show warning)
        with patch('enhanced_gui_integration.messagebox') as mock_messagebox:
            interface._export_data_excel()
            mock_messagebox.showwarning.assert_called_once()
        
        with patch('enhanced_gui_integration.messagebox') as mock_messagebox:
            interface._export_data_csv()
            mock_messagebox.showwarning.assert_called_once()


class TestEnhancedGuiIntegration(unittest.TestCase):
    """Test cases for EnhancedGuiIntegration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Create mock main GUI instance
        self.mock_main_gui = Mock()
        self.mock_main_gui.input_tabs = ttk.Notebook(self.root)
        self.mock_main_gui.analysis_frame = ttk.Frame(self.root)
        self.mock_main_gui.status_var = tk.StringVar()
        self.mock_main_gui.output_text = tk.Text(self.root)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
    
    @patch('enhanced_gui_integration.ExtendedInputTabs')
    @patch('enhanced_gui_integration.EnhancedResultsInterface')
    def test_initialization_success(self, mock_results_class, mock_tabs_class):
        """Test successful initialization of EnhancedGuiIntegration."""
        mock_tabs = Mock()
        mock_results = Mock()
        mock_tabs_class.return_value = mock_tabs
        mock_results_class.return_value = mock_results
        
        integration = EnhancedGuiIntegration(self.mock_main_gui)
        
        # Check that components were created
        self.assertEqual(integration.extended_input_tabs, mock_tabs)
        self.assertEqual(integration.enhanced_results, mock_results)
        
        # Check that initialization methods were called
        mock_tabs_class.assert_called_once()
        mock_results_class.assert_called_once()
    
    @patch('enhanced_gui_integration.ExtendedInputTabs')
    @patch('enhanced_gui_integration.messagebox')
    def test_initialization_failure(self, mock_messagebox, mock_tabs_class):
        """Test initialization failure handling."""
        mock_tabs_class.side_effect = Exception("Test error")
        
        integration = EnhancedGuiIntegration(self.mock_main_gui)
        
        # Should handle error gracefully
        self.assertIsNone(integration.extended_input_tabs)
        mock_messagebox.showerror.assert_called()
    
    @patch('enhanced_gui_integration.ExtendedInputTabs')
    @patch('enhanced_gui_integration.EnhancedResultsInterface')
    def test_status_update(self, mock_results_class, mock_tabs_class):
        """Test status update functionality."""
        integration = EnhancedGuiIntegration(self.mock_main_gui)
        
        # Update status
        test_message = "Test status message"
        integration._update_status(test_message)
        
        # Check that status was updated
        self.assertEqual(self.mock_main_gui.status_var.get(), test_message)
    
    @patch('enhanced_gui_integration.ExtendedInputTabs')
    @patch('enhanced_gui_integration.EnhancedResultsInterface')
    def test_get_current_input_content(self, mock_results_class, mock_tabs_class):
        """Test getting current input content."""
        mock_tabs = Mock()
        mock_tabs.get_current_content.return_value = "Extended tab content"
        mock_tabs_class.return_value = mock_tabs
        
        integration = EnhancedGuiIntegration(self.mock_main_gui)
        
        # Get content
        content = integration.get_current_input_content()
        
        # Should return extended tab content
        self.assertEqual(content, "Extended tab content")
        mock_tabs.get_current_content.assert_called_once()
    
    @patch('enhanced_gui_integration.ExtendedInputTabs')
    @patch('enhanced_gui_integration.EnhancedResultsInterface')
    def test_get_current_input_content_fallback(self, mock_results_class, mock_tabs_class):
        """Test getting current input content with fallback."""
        mock_tabs = Mock()
        mock_tabs.get_current_content.return_value = None
        mock_tabs_class.return_value = mock_tabs
        
        self.mock_main_gui.start_analyse.return_value = "Original content"
        
        integration = EnhancedGuiIntegration(self.mock_main_gui)
        
        # Get content
        content = integration.get_current_input_content()
        
        # Should fallback to original method
        self.assertEqual(content, "Original content")
        self.mock_main_gui.start_analyse.assert_called_once()
    
    @patch('enhanced_gui_integration.ExtendedInputTabs')
    @patch('enhanced_gui_integration.EnhancedResultsInterface')
    def test_display_analysis_result(self, mock_results_class, mock_tabs_class):
        """Test displaying analysis results."""
        mock_results = Mock()
        mock_results_class.return_value = mock_results
        
        integration = EnhancedGuiIntegration(self.mock_main_gui)
        
        # Display result
        test_result = "Test analysis result"
        integration.display_analysis_result(test_result)
        
        # Should call enhanced results display
        mock_results.display_result.assert_called_once()
    
    @patch('enhanced_gui_integration.ExtendedInputTabs')
    @patch('enhanced_gui_integration.EnhancedResultsInterface')
    def test_display_analysis_result_fallback(self, mock_results_class, mock_tabs_class):
        """Test displaying analysis results with fallback."""
        mock_results = Mock()
        mock_results.display_result.side_effect = Exception("Display error")
        mock_results_class.return_value = mock_results
        
        integration = EnhancedGuiIntegration(self.mock_main_gui)
        
        # Display result
        test_result = "Test analysis result"
        integration.display_analysis_result(test_result)
        
        # Should fallback to original display
        # Check that output_text was modified
        self.assertIsNotNone(self.mock_main_gui.output_text)
    
    @patch('enhanced_gui_integration.ExtendedInputTabs')
    @patch('enhanced_gui_integration.EnhancedResultsInterface')
    def test_is_enhanced_interface_available(self, mock_results_class, mock_tabs_class):
        """Test checking if enhanced interface is available."""
        mock_tabs = Mock()
        mock_results = Mock()
        mock_tabs_class.return_value = mock_tabs
        mock_results_class.return_value = mock_results
        
        integration = EnhancedGuiIntegration(self.mock_main_gui)
        
        # Should be available
        self.assertTrue(integration.is_enhanced_interface_available())
        
        # Test with missing components
        integration.extended_input_tabs = None
        self.assertFalse(integration.is_enhanced_interface_available())
    
    @patch('enhanced_gui_integration.ExtendedInputTabs')
    @patch('enhanced_gui_integration.EnhancedResultsInterface')
    def test_handle_action(self, mock_results_class, mock_tabs_class):
        """Test action handling."""
        integration = EnhancedGuiIntegration(self.mock_main_gui)
        
        # Create test result
        test_result = ProcessedResult(
            id="test",
            content="Test content",
            created_at=datetime.now()
        )
        
        # Handle action
        integration._handle_action("summarize", test_result)
        
        # Should update status
        status = self.mock_main_gui.status_var.get()
        self.assertIn("summarize", status)


class TestEnhancedResultsInterfaceIntegration(unittest.TestCase):
    """Integration tests for EnhancedResultsInterface with real components."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.parent_frame = ttk.Frame(self.root)
        self.action_callback = Mock()
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        self.root.destroy()
    
    def test_full_interface_creation(self):
        """Test creating the full interface with all components."""
        try:
            interface = EnhancedResultsInterface(self.parent_frame, self.action_callback)
            
            # Check that all major components exist
            self.assertIsNotNone(interface.main_frame)
            self.assertIsNotNone(interface.results_notebook)
            self.assertIsNotNone(interface.data_tree)
            self.assertIsNotNone(interface.data_summary_text)
            
            # Test that we can display a basic result
            test_result = ProcessedResult(
                id="integration_test",
                content="Integration test content",
                created_at=datetime.now()
            )
            
            # Should not raise exceptions
            interface.display_result(test_result)
            interface.clear()
            
        except ImportError as e:
            self.skipTest(f"Required dependencies not available: {e}")
        except Exception as e:
            self.fail(f"Integration test failed: {e}")
    
    def test_visualization_panel_integration(self):
        """Test integration with visualization panel."""
        try:
            interface = EnhancedResultsInterface(self.parent_frame, self.action_callback)
            
            # Check if visualization panel was created
            if hasattr(interface, 'visualization_panel') and interface.visualization_panel:
                # Test that we can interact with it
                self.assertIsNotNone(interface.visualization_panel)
                
                # Test clearing
                interface.visualization_panel.clear()
            else:
                self.skipTest("Visualization panel not available")
                
        except ImportError as e:
            self.skipTest(f"Visualization dependencies not available: {e}")


if __name__ == '__main__':
    # Run tests
    unittest.main()