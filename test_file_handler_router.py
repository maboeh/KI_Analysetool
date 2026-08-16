"""
Tests for FileHandlerRouter class.
"""

import unittest
import pandas as pd
import os
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

from file_handler_router import FileHandlerRouter, FileTypeInfo, ProcessingResult


class TestFileHandlerRouter(unittest.TestCase):
    """Test cases for FileHandlerRouter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = FileHandlerRouter()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files of different types
        self._create_test_files()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove test files
        for file_path in self.test_files.values():
            if os.path.exists(file_path):
                os.remove(file_path)
        os.rmdir(self.temp_dir)
    
    def _create_test_files(self):
        """Create test files of different formats."""
        self.test_files = {}
        
        # Create CSV file
        csv_data = pd.DataFrame({
            'Name': ['Alice', 'Bob', 'Charlie'],
            'Age': [25, 30, 35],
            'City': ['Berlin', 'München', 'Hamburg']
        })
        self.test_files['csv'] = os.path.join(self.temp_dir, "test.csv")
        csv_data.to_csv(self.test_files['csv'], index=False)
        
        # Create Excel file
        self.test_files['excel'] = os.path.join(self.temp_dir, "test.xlsx")
        csv_data.to_excel(self.test_files['excel'], index=False)
        
        # Create image file
        self.test_files['image'] = os.path.join(self.temp_dir, "test.png")
        img = Image.new('RGB', (200, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((20, 30), 'Test Image', fill='black')
        img.save(self.test_files['image'])
        
        # Create TSV file
        self.test_files['tsv'] = os.path.join(self.temp_dir, "test.tsv")
        csv_data.to_csv(self.test_files['tsv'], sep='\t', index=False)
        
        # Create text file that looks like CSV
        self.test_files['txt_csv'] = os.path.join(self.temp_dir, "test.txt")
        with open(self.test_files['txt_csv'], 'w') as f:
            f.write("col1,col2,col3\nval1,val2,val3\nval4,val5,val6")
        
        # Create unsupported file
        self.test_files['unsupported'] = os.path.join(self.temp_dir, "test.xyz")
        with open(self.test_files['unsupported'], 'w') as f:
            f.write("Unsupported file content")
    
    def test_detect_file_type_csv(self):
        """Test file type detection for CSV files."""
        file_info = self.router.detect_file_type(self.test_files['csv'])
        
        self.assertIsInstance(file_info, FileTypeInfo)
        self.assertEqual(file_info.file_type, 'csv')
        self.assertTrue(file_info.supported)
        self.assertEqual(file_info.confidence, 1.0)
    
    def test_detect_file_type_excel(self):
        """Test file type detection for Excel files."""
        file_info = self.router.detect_file_type(self.test_files['excel'])
        
        self.assertEqual(file_info.file_type, 'excel')
        self.assertTrue(file_info.supported)
        self.assertEqual(file_info.confidence, 1.0)
    
    def test_detect_file_type_image(self):
        """Test file type detection for image files."""
        file_info = self.router.detect_file_type(self.test_files['image'])
        
        self.assertEqual(file_info.file_type, 'image')
        self.assertTrue(file_info.supported)
        self.assertEqual(file_info.confidence, 1.0)
    
    def test_detect_file_type_tsv(self):
        """Test file type detection for TSV files."""
        file_info = self.router.detect_file_type(self.test_files['tsv'])
        
        self.assertEqual(file_info.file_type, 'csv')  # TSV handled by CSV handler
        self.assertTrue(file_info.supported)
    
    def test_detect_file_type_txt_csv(self):
        """Test file type detection for text files that contain CSV data."""
        file_info = self.router.detect_file_type(self.test_files['txt_csv'])
        
        self.assertEqual(file_info.file_type, 'csv')
        self.assertTrue(file_info.supported)
        self.assertGreater(file_info.confidence, 0.5)
    
    def test_detect_file_type_unsupported(self):
        """Test file type detection for unsupported files."""
        file_info = self.router.detect_file_type(self.test_files['unsupported'])
        
        self.assertEqual(file_info.file_type, 'unknown')
        self.assertFalse(file_info.supported)
        self.assertEqual(file_info.confidence, 0.0)
        self.assertIsNotNone(file_info.error_message)
    
    def test_detect_file_type_nonexistent(self):
        """Test file type detection for non-existent files."""
        file_info = self.router.detect_file_type("nonexistent.csv")
        
        self.assertFalse(file_info.supported)
        self.assertIn("does not exist", file_info.error_message)
    
    def test_get_supported_extensions(self):
        """Test getting supported file extensions."""
        extensions = self.router.get_supported_extensions()
        
        self.assertIsInstance(extensions, dict)
        
        # Check that we have handlers
        if 'csv' in self.router.handlers:
            self.assertIn('csv', extensions)
            self.assertIn('.csv', extensions['csv'])
        
        if 'excel' in self.router.handlers:
            self.assertIn('excel', extensions)
            self.assertIn('.xlsx', extensions['excel'])
        
        if 'image' in self.router.handlers:
            self.assertIn('image', extensions)
            self.assertIn('.png', extensions['image'])
    
    def test_process_file_csv(self):
        """Test processing a CSV file."""
        result = self.router.process_file(self.test_files['csv'])
        
        self.assertIsInstance(result, ProcessingResult)
        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'csv')
        self.assertIsNotNone(result.content)
        self.assertIsNotNone(result.structured_data)
        self.assertIn("CSV-Daten:", result.content)
    
    def test_process_file_excel(self):
        """Test processing an Excel file."""
        result = self.router.process_file(self.test_files['excel'])
        
        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'excel')
        self.assertIsNotNone(result.content)
        self.assertIn("Excel-Daten:", result.content)
    
    def test_process_file_image(self):
        """Test processing an image file."""
        result = self.router.process_file(self.test_files['image'])
        
        # Note: This might fail if tesseract is not properly configured
        if result.success:
            self.assertEqual(result.file_type, 'image')
            self.assertIsNotNone(result.content)
            self.assertIn("Bild-/Dokument-Daten:", result.content)
        else:
            # If OCR fails, that's acceptable for testing
            self.assertEqual(result.file_type, 'image')
    
    def test_process_file_unsupported(self):
        """Test processing an unsupported file."""
        result = self.router.process_file(self.test_files['unsupported'])
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
    
    def test_process_multiple_files_same_type(self):
        """Test processing multiple files of the same type."""
        csv_files = [self.test_files['csv'], self.test_files['tsv']]
        result = self.router.process_multiple_files(csv_files, combine_similar=True)
        
        self.assertTrue(result['success'])
        self.assertGreater(result['files_processed'], 0)
        
        # Should have combined CSV results
        if 'csv' in result['combined_results']:
            combined = result['combined_results']['csv']
            self.assertEqual(combined['type'], 'combined')
            self.assertEqual(len(combined['files']), 2)
    
    def test_process_multiple_files_different_types(self):
        """Test processing multiple files of different types."""
        mixed_files = [self.test_files['csv'], self.test_files['excel'], self.test_files['image']]
        result = self.router.process_multiple_files(mixed_files, combine_similar=False)
        
        self.assertTrue(result['success'])
        self.assertGreater(len(result['individual_results']), 0)
        
        # Should have individual results for each file
        for file_path in mixed_files:
            if file_path in result['individual_results']:
                individual_result = result['individual_results'][file_path]
                # Some might fail (like image OCR), but structure should be correct
                self.assertIsInstance(individual_result, ProcessingResult)
    
    def test_process_multiple_files_with_errors(self):
        """Test processing multiple files including unsupported ones."""
        mixed_files = [self.test_files['csv'], self.test_files['unsupported']]
        result = self.router.process_multiple_files(mixed_files)
        
        self.assertTrue(result['success'])
        
        # Should have processed the CSV file
        self.assertGreater(result['files_processed'], 0)
        
        # Should have error for unsupported file
        unsupported_result = result['individual_results'][self.test_files['unsupported']]
        self.assertFalse(unsupported_result.success)
    
    def test_get_analysis_content_single_file(self):
        """Test getting analysis content for a single file."""
        content = self.router.get_analysis_content(self.test_files['csv'])
        
        self.assertIsInstance(content, str)
        self.assertIn("CSV-Daten:", content)
        self.assertIn("Alice", content)  # Should contain data from the test file
    
    def test_get_analysis_content_multiple_files(self):
        """Test getting analysis content for multiple files."""
        files = [self.test_files['csv'], self.test_files['excel']]
        content = self.router.get_analysis_content(files)
        
        self.assertIsInstance(content, str)
        self.assertIn("Multi-Datei-Analyse:", content)
        self.assertIn("Verarbeitete Dateien:", content)
    
    def test_get_analysis_content_unsupported_file(self):
        """Test getting analysis content for unsupported file."""
        content = self.router.get_analysis_content(self.test_files['unsupported'])
        
        self.assertIn("Fehler beim Verarbeiten", content)
    
    def test_get_handler_info(self):
        """Test getting handler information."""
        info = self.router.get_handler_info()
        
        self.assertIsInstance(info, dict)
        self.assertIn('available_handlers', info)
        self.assertIn('supported_extensions', info)
        self.assertIn('handler_details', info)
        
        # Should have at least one handler
        self.assertGreater(len(info['available_handlers']), 0)
    
    def test_router_initialization_with_missing_dependencies(self):
        """Test that router handles missing handler dependencies gracefully."""
        # This test ensures the router doesn't crash if some handlers can't be initialized
        router = FileHandlerRouter()
        
        # Should still be able to create router even if some handlers fail
        self.assertIsInstance(router, FileHandlerRouter)
        
        # Should have file type mapping
        self.assertIsInstance(router.file_type_mapping, dict)
    
    def test_edge_case_empty_file_list(self):
        """Test processing empty file list."""
        result = self.router.process_multiple_files([])
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_edge_case_mixed_success_failure(self):
        """Test processing mix of valid and invalid files."""
        files = [
            self.test_files['csv'],  # Valid
            "nonexistent.csv",       # Invalid - doesn't exist
            self.test_files['unsupported']  # Invalid - unsupported type
        ]
        
        result = self.router.process_multiple_files(files)
        
        self.assertTrue(result['success'])  # Overall success even with some failures
        self.assertEqual(result['files_processed'], 1)  # Only CSV should succeed
        self.assertEqual(result['total_files'], 3)


if __name__ == '__main__':
    unittest.main()