"""
Tests for ExcelHandler class.
"""

import unittest
import pandas as pd
import os
import tempfile
from pathlib import Path
from excel_handler import ExcelHandler, ExcelFileInfo, ExcelSheetInfo


class TestExcelHandler(unittest.TestCase):
    """Test cases for ExcelHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = ExcelHandler()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test Excel files
        self.test_xlsx_file = os.path.join(self.temp_dir, "test_data.xlsx")
        self.test_multi_sheet_file = os.path.join(self.temp_dir, "multi_sheet.xlsx")
        
        # Create test data
        self.test_data = pd.DataFrame({
            'Name': ['Alice', 'Bob', 'Charlie', 'Diana'],
            'Age': [25, 30, 35, 28],
            'City': ['Berlin', 'München', 'Hamburg', 'Köln'],
            'Salary': [50000, 60000, 70000, 55000]
        })
        
        # Create single sheet Excel file
        self.test_data.to_excel(self.test_xlsx_file, index=False)
        
        # Create multi-sheet Excel file
        with pd.ExcelWriter(self.test_multi_sheet_file) as writer:
            self.test_data.to_excel(writer, sheet_name='Employees', index=False)
            
            sales_data = pd.DataFrame({
                'Product': ['A', 'B', 'C'],
                'Sales': [100, 200, 150],
                'Revenue': [1000, 2000, 1500]
            })
            sales_data.to_excel(writer, sheet_name='Sales', index=False)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove test files
        for file_path in [self.test_xlsx_file, self.test_multi_sheet_file]:
            if os.path.exists(file_path):
                os.remove(file_path)
        os.rmdir(self.temp_dir)
    
    def test_can_handle_supported_formats(self):
        """Test that handler can identify supported file formats."""
        self.assertTrue(self.handler.can_handle(self.test_xlsx_file))
        
        # Test .xls format support (create a simple .xls file for testing)
        xls_file = os.path.join(self.temp_dir, "test.xls")
        try:
            self.test_data.to_excel(xls_file, index=False, engine='xlwt')
            self.assertTrue(self.handler.can_handle(xls_file))
        except Exception:
            # If .xls creation fails, just test that the extension is recognized
            self.assertTrue('.xls' in self.handler.SUPPORTED_EXTENSIONS)
        finally:
            if os.path.exists(xls_file):
                os.remove(xls_file)
    
    def test_can_handle_unsupported_formats(self):
        """Test that handler rejects unsupported file formats."""
        # Create a text file
        txt_file = os.path.join(self.temp_dir, "test.txt")
        with open(txt_file, 'w') as f:
            f.write("This is not an Excel file")
        
        self.assertFalse(self.handler.can_handle(txt_file))
        self.assertFalse(self.handler.can_handle("nonexistent.xlsx"))
        
        os.remove(txt_file)
    
    def test_get_file_info_single_sheet(self):
        """Test getting file information for single sheet Excel file."""
        file_info = self.handler.get_file_info(self.test_xlsx_file)
        
        self.assertIsInstance(file_info, ExcelFileInfo)
        self.assertEqual(file_info.file_path, self.test_xlsx_file)
        self.assertEqual(file_info.total_sheets, 1)
        self.assertEqual(len(file_info.sheets), 1)
        
        sheet_info = file_info.sheets[0]
        self.assertIsInstance(sheet_info, ExcelSheetInfo)
        self.assertEqual(sheet_info.rows, 4)  # 4 data rows
        self.assertEqual(sheet_info.columns, 4)  # 4 columns
        self.assertEqual(sheet_info.column_names, ['Name', 'Age', 'City', 'Salary'])
        self.assertEqual(len(sheet_info.preview_data), 4)
    
    def test_get_file_info_multi_sheet(self):
        """Test getting file information for multi-sheet Excel file."""
        file_info = self.handler.get_file_info(self.test_multi_sheet_file)
        
        self.assertEqual(file_info.total_sheets, 2)
        self.assertEqual(len(file_info.sheets), 2)
        
        # Check sheet names
        sheet_names = [sheet.name for sheet in file_info.sheets]
        self.assertIn('Employees', sheet_names)
        self.assertIn('Sales', sheet_names)
    
    def test_read_sheet_default(self):
        """Test reading default sheet from Excel file."""
        df = self.handler.read_sheet(self.test_xlsx_file)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 4)
        self.assertEqual(list(df.columns), ['Name', 'Age', 'City', 'Salary'])
        self.assertEqual(df.iloc[0]['Name'], 'Alice')
    
    def test_read_sheet_specific(self):
        """Test reading specific sheet from multi-sheet Excel file."""
        df = self.handler.read_sheet(self.test_multi_sheet_file, 'Sales')
        
        self.assertEqual(len(df), 3)
        self.assertEqual(list(df.columns), ['Product', 'Sales', 'Revenue'])
        self.assertEqual(df.iloc[0]['Product'], 'A')
    
    def test_read_sheet_with_max_rows(self):
        """Test reading sheet with row limit."""
        df = self.handler.read_sheet(self.test_xlsx_file, max_rows=2)
        
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['Name'], 'Alice')
        self.assertEqual(df.iloc[1]['Name'], 'Bob')
    
    def test_get_sheet_names(self):
        """Test getting sheet names from Excel file."""
        sheet_names = self.handler.get_sheet_names(self.test_multi_sheet_file)
        
        self.assertEqual(len(sheet_names), 2)
        self.assertIn('Employees', sheet_names)
        self.assertIn('Sales', sheet_names)
    
    def test_extract_content_for_analysis(self):
        """Test extracting content in analysis-ready format."""
        content = self.handler.extract_content_for_analysis(self.test_xlsx_file)
        
        self.assertIn("Excel-Daten:", content)
        self.assertIn("Zeilen: 4, Spalten: 4", content)
        self.assertIn("Name | Age | City | Salary", content)
        self.assertIn("Alice | 25 | Berlin | 50000", content)
    
    def test_extract_content_without_headers(self):
        """Test extracting content without headers."""
        content = self.handler.extract_content_for_analysis(
            self.test_xlsx_file, 
            include_headers=False
        )
        
        self.assertNotIn("Excel-Daten:", content)
        self.assertIn("Name | Age | City | Salary", content)
        self.assertIn("Alice | 25 | Berlin | 50000", content)
    
    def test_convert_to_structured_data(self):
        """Test converting Excel data to structured format."""
        structured_data = self.handler.convert_to_structured_data(self.test_xlsx_file)
        
        self.assertEqual(structured_data['source_type'], 'excel')
        self.assertEqual(structured_data['source_file'], self.test_xlsx_file)
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
    
    def test_error_handling_invalid_file(self):
        """Test error handling for invalid files."""
        with self.assertRaises(FileNotFoundError):
            self.handler.get_file_info("nonexistent.xlsx")
        
        with self.assertRaises(ValueError):
            self.handler.read_sheet("nonexistent.xlsx")
    
    def test_error_handling_unsupported_format(self):
        """Test error handling for unsupported file formats."""
        txt_file = os.path.join(self.temp_dir, "test.txt")
        with open(txt_file, 'w') as f:
            f.write("Not an Excel file")
        
        with self.assertRaises(ValueError):
            self.handler.get_file_info(txt_file)
        
        os.remove(txt_file)
    
    def test_large_file_handling(self):
        """Test handling of files with many rows."""
        # Create a larger dataset
        large_data = pd.DataFrame({
            'ID': range(1000),
            'Value': [f"Value_{i}" for i in range(1000)],
            'Number': range(1000, 2000)
        })
        
        large_file = os.path.join(self.temp_dir, "large_data.xlsx")
        large_data.to_excel(large_file, index=False)
        
        try:
            # Test that it can handle the file
            file_info = self.handler.get_file_info(large_file)
            self.assertEqual(file_info.sheets[0].rows, 1000)
            
            # Test that preview is limited
            self.assertLessEqual(len(file_info.sheets[0].preview_data), 10)
            
            # Test content extraction limits rows
            content = self.handler.extract_content_for_analysis(large_file)
            self.assertIn("weitere Zeilen", content)
            
        finally:
            os.remove(large_file)
    
    def test_unnamed_columns_handling(self):
        """Test handling of unnamed columns in Excel files."""
        # Create DataFrame with unnamed columns
        data_with_unnamed = pd.DataFrame(
            [[1, 2, 3, 4], [5, 6, 7, 8]],
            columns=[None, None, None, None]
        )
        
        unnamed_file = os.path.join(self.temp_dir, "unnamed_cols.xlsx")
        data_with_unnamed.to_excel(unnamed_file, index=False)
        
        try:
            df = self.handler.read_sheet(unnamed_file)
            
            # Check that unnamed columns are renamed
            for col in df.columns:
                self.assertTrue(col.startswith('Column_'))
            
        finally:
            os.remove(unnamed_file)


if __name__ == '__main__':
    unittest.main()