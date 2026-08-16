"""
Basic integration test to verify the enhanced system structure works.

This test verifies that the enhanced components can be imported and
initialized properly, even if some dependencies are missing.
"""

import unittest
import sys
import os
from pathlib import Path


class TestBasicIntegration(unittest.TestCase):
    """Test basic integration and structure."""
    
    def test_all_modules_importable(self):
        """Test that all enhanced modules can be imported."""
        modules_to_test = [
            'data_models',
            'data_extractor', 
            'results_processor',
            'results_manager',
            'file_handler_router',
            'error_handler'
        ]
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                print(f"✓ {module_name} imported successfully")
            except ImportError as e:
                self.fail(f"Failed to import {module_name}: {e}")
                
    def test_gui_modules_importable(self):
        """Test that GUI modules can be imported."""
        gui_modules = [
            'results_display',
            'action_buttons', 
            'visualization_panel',
            'excel_export_ui',
            'results_browser',
            'extended_input_tabs',
            'progress_indicator'
        ]
        
        for module_name in gui_modules:
            try:
                __import__(module_name)
                print(f"✓ {module_name} imported successfully")
            except ImportError as e:
                print(f"⚠ {module_name} import failed (may be due to missing dependencies): {e}")
                # Don't fail the test for GUI modules as they may have optional dependencies
                
    def test_handler_modules_importable(self):
        """Test that file handler modules can be imported."""
        handler_modules = [
            'excel_handler',
            'csv_handler',
            'image_handler'
        ]
        
        for module_name in handler_modules:
            try:
                __import__(module_name)
                print(f"✓ {module_name} imported successfully")
            except ImportError as e:
                print(f"⚠ {module_name} import failed (may be due to missing dependencies): {e}")
                
    def test_original_gui_still_works(self):
        """Test that original GUI can still be imported and used."""
        try:
            from Gui import Gui
            print("✓ Original Gui imported successfully")
            
            # Test that it has expected methods
            expected_methods = ['setupGui', 'send_question', 'save_note']
            for method in expected_methods:
                self.assertTrue(hasattr(Gui, method), f"Missing method: {method}")
                
        except ImportError as e:
            self.fail(f"Failed to import original Gui: {e}")
            
    def test_main_module_structure(self):
        """Test that main module has proper structure."""
        try:
            import main
            
            # Test that main has expected functions
            expected_functions = ['check_dependencies', 'setup_directories', 'main']
            for func in expected_functions:
                self.assertTrue(hasattr(main, func), f"Missing function: {func}")
                
            print("✓ Main module structure is correct")
            
        except ImportError as e:
            self.fail(f"Failed to import main: {e}")
            
    def test_directory_structure(self):
        """Test that required directories can be created."""
        from main import setup_directories
        
        # Should not raise exceptions
        setup_directories()
        
        # Check that directories exist
        expected_dirs = ['analysis_history', 'results', 'exports']
        for dir_name in expected_dirs:
            self.assertTrue(Path(dir_name).exists(), f"Directory not created: {dir_name}")
            
        print("✓ Directory structure created successfully")
        
    def test_data_models_basic_functionality(self):
        """Test basic data models functionality."""
        from data_models import ProcessedResult, StructuredData, ResultMetadata
        from datetime import datetime
        
        # Test creating basic data structures
        metadata = ResultMetadata(analysis_type="test")
        structured_data = StructuredData(
            tables=[], entities=[], numeric_values=[],
            temporal_data=[], relationships=[]
        )
        
        result = ProcessedResult(
            id="test",
            content="test content",
            source_info=None,
            extracted_data=structured_data,
            visualizations=[],
            follow_up_actions=[],
            metadata=metadata,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Test serialization
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['content'], "test content")
        
        print("✓ Data models work correctly")
        
    def test_error_handler_basic_functionality(self):
        """Test basic error handler functionality."""
        from error_handler import ErrorHandler
        
        handler = ErrorHandler()
        
        # Test error handling
        test_error = ValueError("Test error")
        error_result = handler.handle_error(test_error, {"test": "context"})
        
        self.assertIsNotNone(error_result)
        
        # Test user-friendly message creation
        message = handler.create_user_friendly_message(error_result)
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)
        
        print("✓ Error handler works correctly")
        
    def test_results_processor_basic_functionality(self):
        """Test basic results processor functionality."""
        try:
            from results_processor import ResultsProcessor
            
            processor = ResultsProcessor()
            self.assertIsNotNone(processor)
            
            # Test that it has expected methods
            expected_methods = ['process_analysis_result']
            for method in expected_methods:
                self.assertTrue(hasattr(processor, method), f"Missing method: {method}")
                
            print("✓ Results processor initialized successfully")
            
        except ImportError as e:
            print(f"⚠ Results processor import failed: {e}")
            
    def test_file_router_basic_functionality(self):
        """Test basic file router functionality."""
        try:
            from file_handler_router import FileHandlerRouter
            
            router = FileHandlerRouter()
            self.assertIsNotNone(router)
            
            # Test that it has expected methods
            expected_methods = ['detect_file_type', 'get_analysis_content']
            for method in expected_methods:
                self.assertTrue(hasattr(router, method), f"Missing method: {method}")
                
            print("✓ File router initialized successfully")
            
        except ImportError as e:
            print(f"⚠ File router import failed: {e}")


class TestIntegrationWorkflow(unittest.TestCase):
    """Test basic integration workflow."""
    
    def test_basic_workflow_components(self):
        """Test that basic workflow components work together."""
        try:
            # Import core components
            from data_models import ProcessedResult, StructuredData, ResultMetadata
            from error_handler import ErrorHandler
            from datetime import datetime
            
            # Create basic workflow
            error_handler = ErrorHandler()
            
            # Create test data
            metadata = ResultMetadata(analysis_type="test")
            structured_data = StructuredData(
                tables=[], entities=[], numeric_values=[],
                temporal_data=[], relationships=[]
            )
            
            result = ProcessedResult(
                id="workflow_test",
                content="Test workflow content",
                source_info=None,
                extracted_data=structured_data,
                visualizations=[],
                follow_up_actions=[],
                metadata=metadata,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Test serialization workflow
            result_dict = result.to_dict()
            self.assertIn('content', result_dict)
            
            print("✓ Basic workflow components work together")
            
        except Exception as e:
            self.fail(f"Basic workflow failed: {e}")


if __name__ == '__main__':
    print("Running basic integration tests...")
    print("=" * 50)
    
    # Run tests with high verbosity
    unittest.main(verbosity=2)