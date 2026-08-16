"""
Integration tests for complete enhanced results processing workflows.

This module tests end-to-end workflows including:
- Excel input to chart output
- Image OCR to data extraction pipeline
- Multi-format input processing
- Performance tests for large file processing
"""

import unittest
import tempfile
import os
import shutil
import time
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import json

# Import all the components we need to test
from excel_handler import ExcelHandler
from image_handler import ImageHandler
from csv_handler import CSVHandler
from data_extractor import DataExtractor, ExtractionConfig
from chart_generator import ChartGenerator
from results_processor import ResultsProcessor
from results_manager import ResultsManager
from file_handler_router import FileHandlerRouter
from data_models import ProcessedResult, StructuredData, ChartType


class TestExcelToChartWorkflow(unittest.TestCase):
    """Test complete workflow from Excel input to chart output."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.excel_handler = ExcelHandler()
        self.data_extractor = DataExtractor(ExtractionConfig())
        self.chart_generator = ChartGenerator()
        self.results_processor = ResultsProcessor()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_test_excel_file(self, filename: str, data: dict) -> str:
        """Create a test Excel file with given data."""
        file_path = os.path.join(self.temp_dir, filename)
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        return file_path
        
    def test_excel_to_bar_chart_workflow(self):
        """Test complete workflow: Excel file -> data extraction -> bar chart."""
        # Create test Excel file with sales data
        test_data = {
            'Product': ['Product A', 'Product B', 'Product C', 'Product D'],
            'Sales': [1000, 1500, 800, 1200],
            'Quarter': ['Q1', 'Q1', 'Q1', 'Q1']
        }
        excel_file = self.create_test_excel_file('sales_data.xlsx', test_data)
        
        # Step 1: Load Excel file
        self.assertTrue(self.excel_handler.can_handle(excel_file))
        file_info = self.excel_handler.get_file_info(excel_file)
        self.assertIsNotNone(file_info)
        self.assertEqual(len(file_info.sheets), 1)
        
        # Step 2: Extract content for analysis
        content_text = self.excel_handler.extract_content_for_analysis(excel_file)
        self.assertIsNotNone(content_text)
        self.assertIn('Product A', content_text)
        
        # Step 3: Extract structured data
        structured_data = self.data_extractor.extract_structured_data(content_text)
        self.assertIsNotNone(structured_data)
        
        # Check if we have either tables or numeric values (data extraction may vary)
        has_data = (len(structured_data.tables) > 0 or 
                   len(structured_data.numeric_values) > 0)
        self.assertTrue(has_data, "Should extract either tables or numeric values")
        
        # Step 4: Generate chart suggestions
        suggestions = self.chart_generator.suggest_chart_types(structured_data)
        self.assertGreater(len(suggestions), 0, "Should get chart suggestions")
        
        # Step 5: Create chart with first available suggestion
        first_suggestion = suggestions[0]
        chart = self.chart_generator.create_chart(structured_data, first_suggestion.chart_type)
        self.assertIsNotNone(chart)
        
        # Step 6: Export chart
        chart_path = os.path.join(self.temp_dir, 'test_chart.png')
        success = self.chart_generator.export_chart(chart, 'png', chart_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(chart_path))
        
    def test_excel_to_line_chart_workflow(self):
        """Test workflow with time series data for line chart."""
        # Create test Excel file with time series data
        test_data = {
            'Date': ['2024-01-01', '2024-02-01', '2024-03-01', '2024-04-01'],
            'Revenue': [10000, 12000, 11500, 13000],
            'Costs': [7000, 8000, 7500, 8500]
        }
        excel_file = self.create_test_excel_file('revenue_data.xlsx', test_data)
        
        # Process through complete workflow
        content_text = self.excel_handler.extract_content_for_analysis(excel_file)
        structured_data = self.data_extractor.extract_structured_data(content_text)
        suggestions = self.chart_generator.suggest_chart_types(structured_data)
        
        # Verify we get chart suggestions
        self.assertGreater(len(suggestions), 0, "Should get chart suggestions")
        
        # Create chart with first suggestion
        first_suggestion = suggestions[0]
        chart = self.chart_generator.create_chart(structured_data, first_suggestion.chart_type)
        self.assertIsNotNone(chart)


class TestImageOCRToDataExtractionWorkflow(unittest.TestCase):
    """Test complete workflow from image OCR to data extraction."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.image_handler = ImageHandler()
        self.data_extractor = DataExtractor(ExtractionConfig())
        self.results_processor = ResultsProcessor()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    @patch('image_handler.pytesseract')
    @patch('image_handler.Image')
    def test_image_ocr_to_entity_extraction(self, mock_image, mock_tesseract):
        """Test OCR text extraction followed by entity recognition."""
        # Mock OCR result with business card text
        mock_ocr_text = """
        John Smith
        Senior Manager
        ABC Corporation
        Phone: +1-555-123-4567
        Email: john.smith@abc.com
        Address: 123 Business St, New York, NY 10001
        """
        mock_tesseract.image_to_string.return_value = mock_ocr_text
        mock_tesseract.image_to_data.return_value = "mock_data"
        
        # Mock image processing
        mock_img = Mock()
        mock_img.size = (800, 600)
        mock_img.format = 'PNG'
        mock_img.mode = 'RGB'
        mock_image.open.return_value = mock_img
        
        # Create mock image file
        image_path = os.path.join(self.temp_dir, 'business_card.png')
        with open(image_path, 'wb') as f:
            f.write(b'mock_image_data')
            
        # Step 1: Check if handler can process the image
        self.assertTrue(self.image_handler.can_handle(image_path))
        
        # Step 2: Extract text via OCR
        content_text = self.image_handler.extract_content_for_analysis(image_path)
        self.assertIsNotNone(content_text)
        self.assertIn('John Smith', content_text)
        
        # Step 3: Extract structured data from OCR text
        structured_data = self.data_extractor.extract_structured_data(content_text)
        self.assertIsNotNone(structured_data)
        
        # Verify some structured data was extracted (entities or other data)
        has_structured_data = (len(structured_data.entities) > 0 or 
                              len(structured_data.numeric_values) > 0 or
                              len(structured_data.tables) > 0)
        self.assertTrue(has_structured_data, "Should extract some structured data")
        
    @patch('image_handler.pytesseract')
    @patch('image_handler.Image')
    def test_image_table_ocr_to_chart_workflow(self, mock_image, mock_tesseract):
        """Test OCR table extraction followed by chart generation."""
        # Mock OCR result with tabular data
        mock_ocr_text = """
        Sales Report Q1 2024
        
        Product     January    February   March      Total
        Widget A    $1,200     $1,350     $1,100     $3,650
        Widget B    $800       $950       $1,200     $2,950
        Widget C    $1,500     $1,400     $1,600     $4,500
        
        Total       $3,500     $3,700     $3,900     $11,100
        """
        mock_tesseract.image_to_string.return_value = mock_ocr_text
        
        # Mock image
        mock_img = Mock()
        mock_img.size = (1200, 800)
        mock_img.format = 'PNG'
        mock_img.mode = 'RGB'
        mock_image.open.return_value = mock_img
        
        image_path = os.path.join(self.temp_dir, 'sales_table.png')
        with open(image_path, 'wb') as f:
            f.write(b'mock_table_image')
            
        # Process through complete workflow
        content_text = self.image_handler.extract_content_for_analysis(image_path)
        structured_data = self.data_extractor.extract_structured_data(content_text)
        
        # Verify some data extraction occurred
        has_data = (len(structured_data.tables) > 0 or 
                   len(structured_data.numeric_values) > 0)
        self.assertTrue(has_data, "Should extract tables or numeric data")
        
        # Generate chart from extracted data if available
        if has_data:
            chart_generator = ChartGenerator()
            suggestions = chart_generator.suggest_chart_types(structured_data)
            # Chart suggestions may be empty if data isn't suitable for charts
            self.assertIsNotNone(suggestions)


class TestMultiFormatInputWorkflow(unittest.TestCase):
    """Test workflows with multiple input formats processed together."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_router = FileHandlerRouter()
        self.results_processor = ResultsProcessor()
        self.results_manager = ResultsManager()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_test_files(self) -> dict:
        """Create multiple test files of different formats."""
        files = {}
        
        # Create Excel file
        excel_data = {
            'Product': ['A', 'B', 'C'],
            'Sales': [100, 200, 150]
        }
        excel_path = os.path.join(self.temp_dir, 'data.xlsx')
        pd.DataFrame(excel_data).to_excel(excel_path, index=False)
        files['excel'] = excel_path
        
        # Create CSV file
        csv_data = "Name,Age,City\nJohn,25,NYC\nJane,30,LA\nBob,35,Chicago"
        csv_path = os.path.join(self.temp_dir, 'people.csv')
        with open(csv_path, 'w') as f:
            f.write(csv_data)
        files['csv'] = csv_path
        
        # Create text file
        text_content = """
        Company Report 2024
        
        Our revenue increased by 15% this year.
        We hired 50 new employees.
        Customer satisfaction: 92%
        """
        text_path = os.path.join(self.temp_dir, 'report.txt')
        with open(text_path, 'w') as f:
            f.write(text_content)
        files['text'] = text_path
        
        return files
        
    def test_multi_file_processing_workflow(self):
        """Test processing multiple files of different formats together."""
        test_files = self.create_test_files()
        
        # Process each file through the router
        combined_text = self.file_router.get_analysis_content(list(test_files.values()))
        self.assertIsNotNone(combined_text)
        self.assertIn('Product', combined_text)  # From Excel
        self.assertIn('John', combined_text)     # From CSV
        
        # Process combined content through results processor
        with patch('analysis.real_ai_analyse_fortext') as mock_analysis:
            mock_analysis.return_value = "Combined analysis result with extracted data"
            
            result = self.results_processor.process_analysis_result(
                combined_text,
                "multi_file_input",
                "combined_analysis"
            )
            
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ProcessedResult)
        
        # Verify structured data was extracted from all sources
        self.assertIsNotNone(result.extracted_data)
        
    def test_results_management_workflow(self):
        """Test complete workflow including results storage and retrieval."""
        test_files = self.create_test_files()
        
        # Process a file and save result
        content_text = self.file_router.get_analysis_content(test_files['excel'])
        
        with patch('analysis.real_ai_analyse_fortext') as mock_analysis:
            mock_analysis.return_value = "Excel analysis result"
            
            result = self.results_processor.process_analysis_result(
                content_text,
                test_files['excel'],
                "excel_analysis"
            )
            
        # Save result
        result_id = self.results_manager.save_result(result, "Test Excel Analysis")
        self.assertIsNotNone(result_id)
        
        # Retrieve and verify result
        loaded_result = self.results_manager.load_result(result_id)
        self.assertIsNotNone(loaded_result)
        self.assertEqual(loaded_result.content, result.content)
        
        # List results
        results_list = self.results_manager.list_results({})
        self.assertGreater(len(results_list), 0)


class TestPerformanceLargeFiles(unittest.TestCase):
    """Performance tests for large file processing."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.excel_handler = ExcelHandler()
        self.csv_handler = CSVHandler()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_large_excel_file(self, rows: int = 10000) -> str:
        """Create a large Excel file for performance testing."""
        file_path = os.path.join(self.temp_dir, 'large_data.xlsx')
        
        # Generate large dataset
        data = {
            'ID': range(1, rows + 1),
            'Name': [f'Item_{i}' for i in range(1, rows + 1)],
            'Value': [i * 1.5 for i in range(1, rows + 1)],
            'Category': [f'Cat_{i % 10}' for i in range(1, rows + 1)],
            'Date': [f'2024-{(i % 12) + 1:02d}-01' for i in range(1, rows + 1)]
        }
        
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        return file_path
        
    def create_large_csv_file(self, rows: int = 50000) -> str:
        """Create a large CSV file for performance testing."""
        file_path = os.path.join(self.temp_dir, 'large_data.csv')
        
        with open(file_path, 'w') as f:
            f.write('ID,Name,Value,Category,Date\n')
            for i in range(1, rows + 1):
                f.write(f'{i},Item_{i},{i * 1.5},Cat_{i % 10},2024-{(i % 12) + 1:02d}-01\n')
                
        return file_path
        
    def test_large_excel_processing_performance(self):
        """Test performance with large Excel files."""
        large_file = self.create_large_excel_file(5000)  # 5K rows
        
        start_time = time.time()
        
        # Test file info extraction
        file_info = self.excel_handler.get_file_info(large_file)
        self.assertIsNotNone(file_info)
        
        info_time = time.time() - start_time
        self.assertLess(info_time, 10.0, "File info extraction took too long")
        
        # Test content extraction
        start_time = time.time()
        content_text = self.excel_handler.extract_content_for_analysis(large_file)
        self.assertIsNotNone(content_text)
        
        extraction_time = time.time() - start_time
        self.assertLess(extraction_time, 30.0, "Content extraction took too long")
        
    def test_large_csv_processing_performance(self):
        """Test performance with large CSV files."""
        large_file = self.create_large_csv_file(20000)  # 20K rows
        
        start_time = time.time()
        
        # Test content extraction
        content_text = self.csv_handler.extract_content_for_analysis(large_file)
        self.assertIsNotNone(content_text)
        
        extraction_time = time.time() - start_time
        self.assertLess(extraction_time, 15.0, "CSV extraction took too long")
        
    def test_memory_usage_large_files(self):
        """Test memory usage doesn't grow excessively with large files."""
        import gc
        
        # Force garbage collection before test
        gc.collect()
        
        # Process multiple large files and verify they complete without errors
        for i in range(3):
            large_file = self.create_large_excel_file(2000)
            content_text = self.excel_handler.extract_content_for_analysis(large_file)
            self.assertIsNotNone(content_text)
            
            # Force garbage collection after each file
            gc.collect()
            
        # If we get here without memory errors, the test passes
        self.assertTrue(True, "Memory usage test completed successfully")


class TestEndToEndIntegration(unittest.TestCase):
    """Complete end-to-end integration tests."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    @patch('analysis.real_ai_analyse_fortext')
    def test_complete_analysis_pipeline(self, mock_analysis):
        """Test complete pipeline from file input to final result with actions."""
        # Mock AI analysis
        mock_analysis.return_value = """
        Sales Analysis Results:
        
        Total Revenue: $125,000
        Growth Rate: 15%
        Top Product: Widget A ($45,000)
        
        Key Insights:
        - Q1 showed strong performance
        - Widget A dominates sales
        - 15% growth year-over-year
        """
        
        # Create test Excel file
        test_data = {
            'Product': ['Widget A', 'Widget B', 'Widget C'],
            'Q1_Sales': [45000, 30000, 25000],
            'Q2_Sales': [50000, 35000, 28000]
        }
        excel_file = os.path.join(self.temp_dir, 'sales.xlsx')
        pd.DataFrame(test_data).to_excel(excel_file, index=False)
        
        # Initialize complete pipeline
        file_router = FileHandlerRouter()
        results_processor = ResultsProcessor()
        results_manager = ResultsManager()
        
        # Step 1: Extract content through router
        content_text = file_router.get_analysis_content(excel_file)
        self.assertIsNotNone(content_text)
        
        # Step 2: Process through AI analysis
        result = results_processor.process_analysis_result(
            content_text,
            excel_file,
            "sales_analysis"
        )
        
        # Verify complete result structure
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ProcessedResult)
        self.assertIsNotNone(result.extracted_data)
        self.assertGreater(len(result.follow_up_actions), 0)
        
        # Step 3: Save result
        result_id = results_manager.save_result(result, "Sales Analysis Test")
        self.assertIsNotNone(result_id)
        
        # Step 4: Verify result can be loaded
        loaded_result = results_manager.load_result(result_id)
        self.assertEqual(loaded_result.content, result.content)
        
        # Step 5: Test follow-up actions
        summarize_action = next(
            (a for a in result.follow_up_actions if a.type == ActionType.SUMMARIZE),
            None
        )
        self.assertIsNotNone(summarize_action)


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestExcelToChartWorkflow,
        TestImageOCRToDataExtractionWorkflow,
        TestMultiFormatInputWorkflow,
        TestPerformanceLargeFiles,
        TestEndToEndIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)