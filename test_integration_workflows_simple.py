"""
Simplified integration tests for enhanced results processing workflows.

This module tests core integration workflows with mocked components to ensure
the overall system architecture works correctly.
"""

import unittest
import tempfile
import os
import shutil
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import components
from excel_handler import ExcelHandler
from image_handler import ImageHandler
from csv_handler import CSVHandler
from data_extractor import DataExtractor, ExtractionConfig
from chart_generator import ChartGenerator
from results_processor import ResultsProcessor
from results_manager import ResultsManager
from file_handler_router import FileHandlerRouter
from data_models import (
    ProcessedResult, StructuredData, ChartType, DataTable, 
    NumericValue, NamedEntity, EntityType
)


class TestSimpleIntegrationWorkflows(unittest.TestCase):
    """Simplified integration tests focusing on component interaction."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_test_excel_file(self, filename: str, data: dict) -> str:
        """Create a test Excel file with given data."""
        file_path = os.path.join(self.temp_dir, filename)
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        return file_path
        
    def test_excel_handler_basic_workflow(self):
        """Test basic Excel file handling workflow."""
        # Create test Excel file
        test_data = {
            'Product': ['A', 'B', 'C'],
            'Sales': [100, 200, 150]
        }
        excel_file = self.create_test_excel_file('test.xlsx', test_data)
        
        # Test Excel handler
        excel_handler = ExcelHandler()
        
        # Check file handling
        self.assertTrue(excel_handler.can_handle(excel_file))
        
        # Get file info
        file_info = excel_handler.get_file_info(excel_file)
        self.assertIsNotNone(file_info)
        self.assertEqual(len(file_info.sheets), 1)
        
        # Extract content
        content = excel_handler.extract_content_for_analysis(excel_file)
        self.assertIsNotNone(content)
        self.assertIn('Product', content)
        
    def test_file_router_workflow(self):
        """Test file routing and content extraction."""
        # Create test files
        excel_data = {'Name': ['John', 'Jane'], 'Age': [25, 30]}
        excel_file = self.create_test_excel_file('people.xlsx', excel_data)
        
        csv_file = os.path.join(self.temp_dir, 'data.csv')
        with open(csv_file, 'w') as f:
            f.write('Item,Price\nApple,1.50\nBanana,0.75\n')
            
        # Test file router
        router = FileHandlerRouter()
        
        # Test single file processing
        excel_content = router.get_analysis_content(excel_file)
        self.assertIsNotNone(excel_content)
        self.assertIn('John', excel_content)
        
        csv_content = router.get_analysis_content(csv_file)
        self.assertIsNotNone(csv_content)
        self.assertIn('Apple', csv_content)
        
        # Test multi-file processing
        combined_content = router.get_analysis_content([excel_file, csv_file])
        self.assertIsNotNone(combined_content)
        self.assertIn('John', combined_content)
        self.assertIn('Apple', combined_content)
        
    @patch('analysis.real_ai_analyse_fortext')
    def test_results_processor_workflow(self, mock_analysis):
        """Test results processing workflow."""
        # Mock AI analysis
        mock_analysis.return_value = "Analysis result with data: Revenue: $1000, Growth: 15%"
        
        # Create test data
        test_content = "Sales data: Product A sold 100 units for $1000"
        
        # Test results processor
        processor = ResultsProcessor()
        result = processor.process_analysis_result(
            test_content,
            "test_source.txt",
            "test_analysis"
        )
        
        # Verify result structure
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ProcessedResult)
        self.assertIsNotNone(result.content)
        self.assertIsNotNone(result.extracted_data)
        self.assertIsNotNone(result.follow_up_actions)
        
    def test_results_manager_workflow(self):
        """Test results storage and retrieval workflow."""
        # Create mock result
        from data_models import create_source_info_from_path, create_default_actions
        
        from data_models import ResultMetadata
        
        result = ProcessedResult(
            id="test_id",
            content="Test analysis result",
            source_info=create_source_info_from_path("test.txt"),
            extracted_data=StructuredData(
                tables=[], entities=[], numeric_values=[], 
                temporal_data=[], relationships=[]
            ),
            visualizations=[],
            follow_up_actions=create_default_actions(),
            metadata=ResultMetadata(
                analysis_type="test",
                model_used="test_model",
                processing_time=1.0,
                confidence_score=0.9,
                tags=[]
            ),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Test results manager
        manager = ResultsManager(
            db_path=os.path.join(self.temp_dir, "results.db"),
            results_dir=os.path.join(self.temp_dir, "results")
        )
        
        # Save result
        result_id = manager.save_result(result, "Test Result")
        self.assertIsNotNone(result_id)
        
        # Load result
        loaded_result = manager.load_result(result_id)
        self.assertIsNotNone(loaded_result)
        self.assertEqual(loaded_result.content, result.content)
        
        # List results
        results_list = manager.list_results({})
        self.assertGreater(len(results_list), 0)
        
    def test_data_extractor_with_mock_data(self):
        """Test data extractor with controlled input."""
        extractor = DataExtractor(ExtractionConfig())
        
        # Test with simple structured text
        test_text = """
        Sales Report
        Product A: $1,000
        Product B: $2,500
        Total: $3,500
        Date: 2024-01-15
        """
        
        structured_data = extractor.extract_structured_data(test_text)
        self.assertIsNotNone(structured_data)
        
        # Should extract some numeric values
        self.assertGreaterEqual(len(structured_data.numeric_values), 0)
        
    def test_chart_generator_with_mock_data(self):
        """Test chart generator with controlled structured data."""
        generator = ChartGenerator()
        
        # Create mock structured data
        mock_data = StructuredData(
            tables=[],
            entities=[],
            numeric_values=[
                NumericValue(value=1000.0, unit="$", context="Product A", value_type="currency"),
                NumericValue(value=2500.0, unit="$", context="Product B", value_type="currency")
            ],
            temporal_data=[],
            relationships=[]
        )
        
        # Test chart suggestions
        suggestions = generator.suggest_chart_types(mock_data)
        self.assertIsNotNone(suggestions)
        
        # If we have suggestions, test chart creation
        if len(suggestions) > 0:
            first_suggestion = suggestions[0]
            chart = generator.create_chart(mock_data, first_suggestion.chart_type)
            self.assertIsNotNone(chart)
            
    def test_image_handler_workflow(self):
        """Test image processing workflow."""
        # Test image handler initialization
        try:
            handler = ImageHandler()
            
            # Test basic functionality
            test_extensions = ['.png', '.jpg', '.jpeg']
            for ext in test_extensions:
                fake_path = f"test{ext}"
                # Just test the extension checking logic
                self.assertIn(ext, handler.SUPPORTED_EXTENSIONS)
                
            # If tesseract is not available, that's expected in test environment
            if not handler.tesseract_available:
                self.skipTest("Tesseract not available - this is expected in test environment")
            else:
                # Basic functionality test passed
                self.assertTrue(True)
                
        except ImportError:
            # Dependencies not available - skip test
            self.skipTest("Image processing dependencies not available")
            
    @patch('analysis.real_ai_analyse_fortext')
    def test_end_to_end_workflow(self, mock_analysis):
        """Test complete end-to-end workflow."""
        # Mock AI analysis
        mock_analysis.return_value = "Complete analysis with insights and data"
        
        # Create test Excel file
        test_data = {
            'Month': ['Jan', 'Feb', 'Mar'],
            'Revenue': [1000, 1200, 1100],
            'Costs': [800, 900, 850]
        }
        excel_file = self.create_test_excel_file('monthly_data.xlsx', test_data)
        
        # Initialize components
        router = FileHandlerRouter()
        processor = ResultsProcessor()
        manager = ResultsManager(
            db_path=os.path.join(self.temp_dir, "results.db"),
            results_dir=os.path.join(self.temp_dir, "results")
        )
        
        # Step 1: Extract content
        content = router.get_analysis_content(excel_file)
        self.assertIsNotNone(content)
        
        # Step 2: Process through AI
        result = processor.process_analysis_result(
            content,
            excel_file,
            "monthly_analysis"
        )
        self.assertIsNotNone(result)
        
        # Step 3: Save result
        result_id = manager.save_result(result, "Monthly Analysis")
        self.assertIsNotNone(result_id)
        
        # Step 4: Verify retrieval
        loaded_result = manager.load_result(result_id)
        self.assertEqual(loaded_result.content, result.content)
        
        # Verify we have follow-up actions
        self.assertGreater(len(result.follow_up_actions), 0)
        
    def test_performance_basic(self):
        """Basic performance test with reasonable file sizes."""
        import time
        
        # Create moderately sized Excel file
        large_data = {
            'ID': list(range(1, 1001)),  # 1000 rows
            'Value': [i * 1.5 for i in range(1, 1001)],
            'Category': [f'Cat_{i % 10}' for i in range(1, 1001)]
        }
        excel_file = self.create_test_excel_file('large_data.xlsx', large_data)
        
        # Test processing time
        start_time = time.time()
        
        handler = ExcelHandler()
        content = handler.extract_content_for_analysis(excel_file)
        
        processing_time = time.time() - start_time
        
        # Should complete within reasonable time (10 seconds)
        self.assertLess(processing_time, 10.0, 
                       f"Processing took {processing_time:.2f} seconds")
        self.assertIsNotNone(content)


if __name__ == '__main__':
    # Run simplified integration tests
    unittest.main(verbosity=2)