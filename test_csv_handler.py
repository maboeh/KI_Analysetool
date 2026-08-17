"""
Tests for CSVHandler class.
"""

import unittest
import pandas as pd
import os
import tempfile
from pathlib import Path
from csv_handler import CSVHandler, CSVInfo, MultiFileResult


class TestCSVHandler(unittest.TestCase):
    """Test cases for CSVHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = CSVHandler()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test CSV files
        self.test_csv_file = os.path.join(self.temp_dir, "test_data.csv")
        self.test_tsv_file = os.path.join(self.temp_dir, "test_data.tsv")
        self.test_semicolon_file = os.path.join(self.temp_dir, "test_semicolon.csv")
        self.test_no_header_file = os.path.join(self.temp_dir, "test_no_header.csv")
        
        # Create test data
        self.test_data = pd.DataFrame({
            'Name': ['Alice', 'Bob', 'Charlie', 'Diana'],
            'Age': [25, 30, 35, 28],
            'City': ['Berlin', 'München', 'Hamburg', 'Köln'],
            'Salary': [50000, 60000, 70000, 55000]
        })
        
        # Create different CSV formats
        self.test_data.to_csv(self.test_csv_file, index=False)  # Comma-separated
        self.test_data.to_csv(self.test_tsv_file, sep='\t', index=False)  # Tab-separated
        self.test_data.to_csv(self.test_semicolon_file, sep=';', index=False)  # Semicolon-separated
        
        # Create file without header
        self.test_data.to_csv(self.test_no_header_file, index=False, header=False)
        
        # Create additional files for multi-file testing
        self.sales_data = pd.DataFrame({
            'Product': ['A', 'B', 'C', 'D'],
            'Sales': [100, 200, 150, 300],
            'Revenue': [1000, 2000, 1500, 3000]
        })
        
        self.sales_file = os.path.join(self.temp_dir, "sales_data.csv")
        self.sales_data.to_csv(self.sales_file, index=False)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove test files
        test_files = [
            self.test_csv_file, self.test_tsv_file, self.test_semicolon_file,
            self.test_no_header_file, self.sales_file
        ]
        for file_path in test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        os.rmdir(self.temp_dir)
    
    def test_can_handle_supported_formats(self):
        """Test that handler can identify supported file formats."""
        self.assertTrue(self.handler.can_handle(self.test_csv_file))
        self.assertTrue(self.handler.can_handle(self.test_tsv_file))
        
        # Test other supported extensions
        txt_file = os.path.join(self.temp_dir, "test.txt")
        with open(txt_file, 'w') as f:
            f.write("col1,col2\nval1,val2")
        
        self.assertTrue(self.handler.can_handle(txt_file))
        os.remove(txt_file)
    
    def test_can_handle_unsupported_formats(self):
        """Test that handler rejects unsupported file formats."""
        # Create a non-CSV file
        xlsx_file = os.path.join(self.temp_dir, "test.xlsx")
        with open(xlsx_file, 'w') as f:
            f.write("This is not a CSV file")
        
        self.assertFalse(self.handler.can_handle(xlsx_file))
        self.assertFalse(self.handler.can_handle("nonexistent.csv"))
        
        os.remove(xlsx_file)
    
    def test_detect_encoding(self):
        """Test encoding detection."""
        encoding = self.handler.detect_encoding(self.test_csv_file)
        self.assertIsInstance(encoding, str)
        self.assertIn(encoding.lower(), ['utf-8', 'ascii', 'latin-1', 'cp1252'])
    
    def test_detect_delimiter_comma(self):
        """Test delimiter detection for comma-separated files."""
        encoding = self.handler.detect_encoding(self.test_csv_file)
        delimiter, has_header = self.handler.detect_delimiter(self.test_csv_file, encoding)
        
        self.assertEqual(delimiter, ',')
        self.assertTrue(has_header)
    
    def test_detect_delimiter_tab(self):
        """Test delimiter detection for tab-separated files."""
        encoding = self.handler.detect_encoding(self.test_tsv_file)
        delimiter, has_header = self.handler.detect_delimiter(self.test_tsv_file, encoding)
        
        self.assertEqual(delimiter, '\t')
        self.assertTrue(has_header)
    
    def test_detect_delimiter_semicolon(self):
        """Test delimiter detection for semicolon-separated files."""
        encoding = self.handler.detect_encoding(self.test_semicolon_file)
        delimiter, has_header = self.handler.detect_delimiter(self.test_semicolon_file, encoding)
        
        self.assertEqual(delimiter, ';')
        self.assertTrue(has_header)
    
    def test_get_file_info(self):
        """Test getting comprehensive file information."""
        file_info = self.handler.get_file_info(self.test_csv_file)
        
        self.assertIsInstance(file_info, CSVInfo)
        self.assertEqual(file_info.file_path, self.test_csv_file)
        self.assertEqual(file_info.delimiter, ',')
        self.assertEqual(file_info.rows, 4)
        self.assertEqual(file_info.columns, 4)
        self.assertEqual(file_info.column_names, ['Name', 'Age', 'City', 'Salary'])
        self.assertTrue(file_info.has_header)
        self.assertEqual(len(file_info.preview_data), 4)
    
    def test_get_file_info_no_header(self):
        """Test getting file information for file without header."""
        file_info = self.handler.get_file_info(self.test_no_header_file)
        
        self.assertFalse(file_info.has_header)
        self.assertEqual(file_info.columns, 4)
        # Should have generated column names
        self.assertTrue(all(col.startswith('Column_') for col in file_info.column_names))
    
    def test_read_csv_with_header(self):
        """Test reading CSV file with header."""
        df = self.handler.read_csv(self.test_csv_file)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 4)
        self.assertEqual(list(df.columns), ['Name', 'Age', 'City', 'Salary'])
        self.assertEqual(df.iloc[0]['Name'], 'Alice')
    
    def test_read_csv_without_header(self):
        """Test reading CSV file without header."""
        df = self.handler.read_csv(self.test_no_header_file)
        
        self.assertEqual(len(df), 4)
        # Should have generated column names
        self.assertTrue(all(col.startswith('Column_') for col in df.columns))
    
    def test_read_csv_with_max_rows(self):
        """Test reading CSV with row limit."""
        df = self.handler.read_csv(self.test_csv_file, max_rows=2)
        
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['Name'], 'Alice')
        self.assertEqual(df.iloc[1]['Name'], 'Bob')
    
    def test_extract_content_for_analysis(self):
        """Test extracting content in analysis-ready format."""
        content = self.handler.extract_content_for_analysis(self.test_csv_file)
        
        self.assertIn("CSV-Daten:", content)
        self.assertIn("Zeilen: 4, Spalten: 4", content)
        self.assertIn("Name | Age | City | Salary", content)
        self.assertIn("Alice | 25 | Berlin | 50000", content)
    
    def test_extract_content_without_headers(self):
        """Test extracting content without metadata headers."""
        content = self.handler.extract_content_for_analysis(
            self.test_csv_file, 
            include_headers=False
        )
        
        self.assertNotIn("CSV-Daten:", content)
        self.assertIn("Name | Age | City | Salary", content)
        self.assertIn("Alice | 25 | Berlin | 50000", content)
    
    def test_convert_to_structured_data(self):
        """Test converting CSV data to structured format."""
        structured_data = self.handler.convert_to_structured_data(self.test_csv_file)
        
        self.assertEqual(structured_data['source_type'], 'csv')
        self.assertEqual(structured_data['source_file'], self.test_csv_file)
        self.assertEqual(structured_data['dimensions']['rows'], 4)
        self.assertEqual(structured_data['dimensions']['columns'], 4)
        self.assertEqual(structured_data['columns'], ['Name', 'Age', 'City', 'Salary'])
        
        # Check data content
        self.assertEqual(len(structured_data['data']), 4)
        self.assertEqual(structured_data['data'][0]['Name'], 'Alice')
        
        # Check summary
        summary = structured_data['summary']
        self.assertIn('Age', summary['numeric_columns'])
        self.assertIn('Salary', summary['numeric_columns'])
        self.assertIn('Name', summary['text_columns'])
        self.assertIn('City', summary['text_columns'])
    
    def test_process_multiple_files_concat(self):
        """Test processing multiple files with concatenation."""
        file_paths = [self.test_csv_file, self.sales_file]
        result = self.handler.process_multiple_files(file_paths, 'concat')
        
        self.assertIsInstance(result, MultiFileResult)
        self.assertEqual(len(result.files_processed), 2)
        self.assertIsNotNone(result.combined_data)
        
        # Should have rows from both files
        self.assertEqual(len(result.combined_data), 8)  # 4 + 4 rows
        
        # Should have source file tracking
        self.assertIn('_source_file', result.combined_data.columns)
    
    def test_process_multiple_files_separate(self):
        """Test processing multiple files separately."""
        file_paths = [self.test_csv_file, self.sales_file]
        result = self.handler.process_multiple_files(file_paths, 'separate')
        
        self.assertEqual(len(result.files_processed), 2)
        self.assertEqual(len(result.individual_results), 2)
        
        # Check individual results
        for file_path in file_paths:
            self.assertIn(file_path, result.individual_results)
            self.assertIn('info', result.individual_results[file_path])
            self.assertIn('structured_data', result.individual_results[file_path])
    
    def test_process_multiple_files_merge(self):
        """Test processing multiple files with merge."""
        # Create files with common columns for merging
        common_data1 = pd.DataFrame({
            'ID': [1, 2, 3],
            'Name': ['Alice', 'Bob', 'Charlie'],
            'Department': ['IT', 'HR', 'Finance']
        })
        
        common_data2 = pd.DataFrame({
            'ID': [1, 2, 4],
            'Salary': [50000, 60000, 55000],
            'Location': ['Berlin', 'München', 'Hamburg']
        })
        
        file1 = os.path.join(self.temp_dir, "employees.csv")
        file2 = os.path.join(self.temp_dir, "salaries.csv")
        
        common_data1.to_csv(file1, index=False)
        common_data2.to_csv(file2, index=False)
        
        try:
            result = self.handler.process_multiple_files([file1, file2], 'merge')
            
            self.assertIsNotNone(result.combined_data)
            # Should have merged on ID column
            self.assertIn('ID', result.combined_data.columns)
            self.assertIn('Name', result.combined_data.columns)
            self.assertIn('Salary', result.combined_data.columns)
            
        finally:
            os.remove(file1)
            os.remove(file2)
    
    def test_extract_combined_content_for_analysis(self):
        """Test extracting combined content for analysis."""
        file_paths = [self.test_csv_file, self.sales_file]
        content = self.handler.extract_combined_content_for_analysis(file_paths)
        
        self.assertIn("Multi-CSV-Datenanalyse:", content)
        self.assertIn("Verarbeitete Dateien: 2", content)
        self.assertIn("test_data.csv", content)
        self.assertIn("sales_data.csv", content)
        self.assertIn("Kombinierte Daten", content)
    
    def test_error_handling_invalid_file(self):
        """Test error handling for invalid files."""
        with self.assertRaises(ValueError):
            self.handler.get_file_info("nonexistent.csv")
        
        with self.assertRaises(ValueError):
            self.handler.read_csv("nonexistent.csv")
    
    def test_error_handling_unsupported_format(self):
        """Test error handling for unsupported file formats."""
        xlsx_file = os.path.join(self.temp_dir, "test.xlsx")
        with open(xlsx_file, 'w') as f:
            f.write("Not a CSV file")
        
        with self.assertRaises(ValueError):
            self.handler.get_file_info(xlsx_file)
        
        os.remove(xlsx_file)
    
    def test_large_file_handling(self):
        """Test handling of files with many rows."""
        # Create a larger dataset
        large_data = pd.DataFrame({
            'ID': range(1000),
            'Value': [f"Value_{i}" for i in range(1000)],
            'Number': range(1000, 2000)
        })
        
        large_file = os.path.join(self.temp_dir, "large_data.csv")
        large_data.to_csv(large_file, index=False)
        
        try:
            # Test that it can handle the file
            file_info = self.handler.get_file_info(large_file)
            self.assertEqual(file_info.rows, 1000)
            
            # Test that preview is limited
            self.assertLessEqual(len(file_info.preview_data), self.handler.MAX_PREVIEW_ROWS)
            
            # Test content extraction limits rows
            content = self.handler.extract_content_for_analysis(large_file)
            self.assertIn("weitere Zeilen", content)
            
        finally:
            os.remove(large_file)
    
    def test_special_characters_handling(self):
        """Test handling of files with special characters."""
        # Create data with special characters
        special_data = pd.DataFrame({
            'Name': ['Müller', 'Schäfer', 'Weiß', 'Größe'],
            'City': ['München', 'Köln', 'Düsseldorf', 'Nürnberg'],
            'Value': [1.5, 2.7, 3.14, 4.0]
        })
        
        special_file = os.path.join(self.temp_dir, "special_chars.csv")
        special_data.to_csv(special_file, index=False, encoding='utf-8')
        
        try:
            # Test reading file with special characters
            df = self.handler.read_csv(special_file)
            self.assertEqual(len(df), 4)
            self.assertEqual(df.iloc[0]['Name'], 'Müller')
            
            # Test file info
            file_info = self.handler.get_file_info(special_file)
            self.assertEqual(file_info.encoding, 'utf-8')
            
        finally:
            os.remove(special_file)
    
    def test_empty_file_handling(self):
        """Test handling of empty files."""
        empty_file = os.path.join(self.temp_dir, "empty.csv")
        with open(empty_file, 'w') as f:
            f.write("")  # Empty file
        
        try:
            with self.assertRaises(ValueError):
                self.handler.get_file_info(empty_file)
        finally:
            os.remove(empty_file)
    
    def test_process_multiple_files_with_errors(self):
        """Test multi-file processing with some invalid files."""
        # Mix valid and invalid files
        invalid_file = os.path.join(self.temp_dir, "invalid.txt")
        with open(invalid_file, 'w') as f:
            f.write("This is not CSV data")
        
        file_paths = [self.test_csv_file, invalid_file, self.sales_file]
        
        try:
            result = self.handler.process_multiple_files(file_paths)
            
            # Should process valid files and report errors for invalid ones
            self.assertEqual(len(result.files_processed), 2)  # Only valid files
            self.assertIn('errors', result.processing_summary)
            
        finally:
            os.remove(invalid_file)


if __name__ == '__main__':
    unittest.main()