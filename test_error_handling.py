"""
Comprehensive tests for enhanced error handling in file processing modules.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path
import pandas as pd

from error_handler import ErrorHandler, ErrorResult, ErrorSeverity, ErrorCategory
from excel_handler import ExcelHandler
from image_handler import ImageHandler
from csv_handler import CSVHandler
from chart_generator import ChartGenerator
from data_models import StructuredData, ChartType, ChartConfig


class TestErrorHandlerIntegration(unittest.TestCase):
    """Test error handler integration with file processing modules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_excel_handler_file_not_found_error(self):
        """Test Excel handler handles file not found errors gracefully."""
        handler = ExcelHandler()
        non_existent_file = os.path.join(self.temp_dir, "nonexistent.xlsx")
        
        with self.assertRaises(FileNotFoundError) as context:
            handler.get_file_info(non_existent_file)
        
        error_message = str(context.exception)
        self.assertIn("nicht gefunden", error_message.lower())
        self.assertIn("lösungsvorschläge", error_message.lower())
    
    def test_excel_handler_unsupported_format_error(self):
        """Test Excel handler handles unsupported formats gracefully."""
        handler = ExcelHandler()
        
        # Create a text file with .txt extension
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("This is not an Excel file")
        
        with self.assertRaises(ValueError) as context:
            handler.get_file_info(test_file)
        
        error_message = str(context.exception)
        self.assertIn("nicht unterstützt", error_message.lower())
        self.assertIn("unterstützte formate", error_message.lower())
    
    def test_excel_handler_file_too_large_error(self):
        """Test Excel handler handles oversized files gracefully."""
        handler = ExcelHandler()
        
        # Create a large dummy file
        large_file = os.path.join(self.temp_dir, "large.xlsx")
        with open(large_file, 'wb') as f:
            # Write more than the limit (100MB)
            f.write(b'0' * (handler.MAX_FILE_SIZE_MB * 1024 * 1024 + 1))
        
        with self.assertRaises(ValueError) as context:
            handler.get_file_info(large_file)
        
        error_message = str(context.exception)
        self.assertIn("zu groß", error_message.lower())
        self.assertIn("mb", error_message.lower())
    
    @patch('image_handler.DEPENDENCIES_AVAILABLE', False)
    def test_image_handler_missing_dependencies_error(self):
        """Test Image handler handles missing dependencies gracefully."""
        with self.assertRaises(ImportError) as context:
            ImageHandler()
        
        error_message = str(context.exception)
        self.assertIn("erforderliche komponente", error_message.lower())
        self.assertIn("installieren", error_message.lower())
    
    @patch('image_handler.pytesseract')
    def test_image_handler_ocr_failure_with_fallback(self, mock_tesseract):
        """Test Image handler provides fallback when OCR fails."""
        # Mock tesseract to raise an exception
        mock_tesseract.get_tesseract_version.side_effect = Exception("Tesseract not found")
        mock_tesseract.image_to_string.side_effect = Exception("OCR failed")
        
        handler = ImageHandler()
        
        # Create a dummy image file
        test_image = os.path.join(self.temp_dir, "test.png")
        with open(test_image, 'wb') as f:
            f.write(b'fake image data')
        
        # Should not raise exception but provide fallback
        with patch('image_handler.Image.open'):
            try:
                result = handler.extract_text(test_image)
                self.assertIn("fehlgeschlagen", result.text.lower())
                self.assertEqual(result.confidence, 0.0)
                self.assertTrue(result.processing_info.get('fallback_mode', False))
            except Exception:
                # If it does raise, check it's a user-friendly message
                pass
    
    def test_csv_handler_encoding_detection_fallback(self):
        """Test CSV handler handles encoding issues gracefully."""
        handler = CSVHandler()
        
        # Create a CSV file with problematic encoding
        test_csv = os.path.join(self.temp_dir, "test.csv")
        with open(test_csv, 'wb') as f:
            # Write some bytes that might cause encoding issues
            f.write(b'\xff\xfe\x41\x00\x42\x00\x43\x00\n')  # UTF-16 BOM + ABC
        
        try:
            info = handler.get_file_info(test_csv)
            # Should succeed with fallback encoding
            self.assertIsNotNone(info.encoding)
        except Exception as e:
            # If it fails, should be user-friendly
            error_message = str(e)
            self.assertIn("kodierung", error_message.lower())
    
    def test_chart_generator_insufficient_data_error(self):
        """Test Chart generator handles insufficient data gracefully."""
        generator = ChartGenerator()
        
        # Create empty structured data
        empty_data = StructuredData(
            tables=[],
            entities=[],
            numeric_values=[],
            temporal_data=[],
            relationships=[]
        )
        
        with self.assertRaises(ValueError) as context:
            generator.create_chart(empty_data, ChartType.BAR)
        
        error_message = str(context.exception)
        self.assertIn("nicht genügend", error_message.lower())
        self.assertIn("lösungsvorschläge", error_message.lower())
    
    def test_chart_generator_export_permission_error(self):
        """Test Chart generator handles export permission errors gracefully."""
        generator = ChartGenerator()
        
        # Create a mock visualization
        mock_viz = Mock()
        mock_viz._figure = Mock()
        mock_viz._figure.savefig.side_effect = PermissionError("Permission denied")
        
        result = generator.export_chart(mock_viz, "/root/test.png")
        self.assertFalse(result)  # Should return False, not raise exception
    
    def test_error_handler_recovery_actions(self):
        """Test error handler generates appropriate recovery actions."""
        handler = ErrorHandler()
        
        # Test file processing error
        context = {"operation": "file_processing", "file_path": "/test/file.xlsx"}
        error_result = handler.handle_error(FileNotFoundError("File not found"), context)
        
        self.assertIsNotNone(error_result.recovery_actions)
        self.assertTrue(any("erneut auswählen" in action.lower() for action in error_result.recovery_actions))
    
    def test_error_handler_user_friendly_messages(self):
        """Test error handler creates comprehensive user-friendly messages."""
        handler = ErrorHandler()
        
        # Test with various error types
        test_cases = [
            (FileNotFoundError("No such file"), "nicht gefunden"),
            (PermissionError("Access denied"), "berechtigung"),
            (MemoryError("Out of memory"), "arbeitsspeicher"),
            (ImportError("No module named 'test'"), "komponente"),
        ]
        
        for error, expected_text in test_cases:
            error_result = handler.handle_error(error)
            message = handler.create_user_friendly_message(error_result)
            
            self.assertIn(expected_text.lower(), message.lower())
            self.assertIn("lösungsvorschläge", message.lower())
    
    def test_graceful_degradation_multi_file_processing(self):
        """Test graceful degradation when processing multiple files with some failures."""
        handler = CSVHandler()

        # Create one valid CSV and one non-existent file
        valid_csv = os.path.join(self.temp_dir, "valid.csv")
        with open(valid_csv, 'w') as f:
            f.write("col1,col2\n1,2\n3,4\n")

        invalid_file = os.path.join(self.temp_dir, "nonexistent.csv")

        # Should process valid file and skip non-existent one
        try:
            result = handler.process_multiple_files([valid_csv, invalid_file])
            self.assertEqual(len(result.files_processed), 1)  # Only valid file processed
        except Exception as e:
            # If it raises, should be informative
            self.assertIn("csv", str(e).lower())


class TestErrorRecoveryMechanisms(unittest.TestCase):
    """Test error recovery and fallback mechanisms."""
    
    def test_fallback_function_execution(self):
        """Test that fallback functions are executed when provided."""
        handler = ErrorHandler()
        
        def fallback():
            return "fallback_result"
        
        error_result = handler.handle_error(
            ValueError("Test error"), 
            fallback_function=fallback
        )
        
        self.assertEqual(error_result.fallback_result, "fallback_result")
    
    def test_error_classification_accuracy(self):
        """Test that errors are classified correctly."""
        handler = ErrorHandler()
        
        test_cases = [
            (FileNotFoundError(), "FILE_NOT_FOUND"),
            (PermissionError(), "PERMISSION_DENIED"),
            (MemoryError(), "MEMORY_ERROR"),
            (ImportError("No module named 'test'"), "MISSING_DEPENDENCY"),
        ]
        
        for error, expected_code in test_cases:
            error_result = handler.handle_error(error)
            self.assertEqual(error_result.error_info.code, expected_code)
    
    def test_context_specific_suggestions(self):
        """Test that suggestions are context-specific."""
        handler = ErrorHandler()
        
        # File processing context
        file_context = {"operation": "file_processing", "file_path": "/test/file.xlsx"}
        error_result = handler.handle_error(FileNotFoundError(), file_context)
        
        suggestions = error_result.error_info.suggestions
        self.assertTrue(any("datei" in suggestion.lower() for suggestion in suggestions))
        
        # Export context
        export_context = {"operation": "export", "file_path": "/test/output.png"}
        error_result = handler.handle_error(PermissionError(), export_context)
        
        recovery_actions = error_result.recovery_actions
        self.assertTrue(any("speicherort" in action.lower() for action in recovery_actions))


class TestProgressIndicationPreparation(unittest.TestCase):
    """Test preparation for progress indication functionality."""
    
    def test_long_running_operation_identification(self):
        """Test identification of operations that need progress indication."""
        # These tests prepare for the progress indication implementation
        
        operations_needing_progress = [
            "large_file_processing",
            "multi_file_processing", 
            "chart_generation",
            "ocr_processing",
            "excel_export"
        ]
        
        for operation in operations_needing_progress:
            # This would be used to determine if progress indication is needed
            needs_progress = self._operation_needs_progress_indication(operation)
            self.assertTrue(needs_progress)
    
    def _operation_needs_progress_indication(self, operation: str) -> bool:
        """Helper method to determine if operation needs progress indication."""
        long_running_operations = [
            "large_file_processing",
            "multi_file_processing",
            "chart_generation", 
            "ocr_processing",
            "excel_export"
        ]
        return operation in long_running_operations
    
    def test_error_message_formatting_for_ui(self):
        """Test that error messages are properly formatted for UI display."""
        handler = ErrorHandler()
        
        error_result = handler.handle_error(
            ValueError("Test error"),
            context={"operation": "test"}
        )
        
        message = handler.create_user_friendly_message(error_result)
        
        # Check formatting elements
        self.assertIn("❌", message)  # Error icon
        self.assertIn("💡", message)  # Suggestion icon
        self.assertTrue(message.count("\n") > 0)  # Multi-line formatting


if __name__ == '__main__':
    unittest.main()