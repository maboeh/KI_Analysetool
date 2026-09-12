"""
Tests for the ResultsProcessor class and integration functions.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import tempfile
import os

from analysis import AnalysisError, AnalysisErrorCode, AnalysisFailure, AnalysisOutcome
from results_processor import (
    ResultsProcessor, create_results_processor, enhanced_analyze_text,
    enhanced_analyze_pdf, enhanced_analyze_content
)
from data_models import (
    ProcessedResult, StructuredData, SourceInfo, ActionType, EntityType,
    NamedEntity, NumericValue, DataTable
)


class TestResultsProcessor(unittest.TestCase):
    """Test cases for ResultsProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = ResultsProcessor()
        
        # Mock the analysis functions
        self.analysis_patcher = patch('results_processor.analysis')
        self.mock_analysis = self.analysis_patcher.start()
        
        # Also mock analysis in follow_up_actions
        self.follow_up_analysis_patcher = patch('follow_up_actions.analysis')
        self.mock_follow_up_analysis = self.follow_up_analysis_patcher.start()
        
        # Set up mock return values
        self.mock_analysis.real_ai_analyse_fortext.return_value = "Test analysis result with 25% improvement and €1,000 budget."
        self.mock_analysis.real_ai_analyse_forpdf.return_value = "PDF analysis result with data table."
        self.mock_analysis.text_extraction_youtube_website.return_value = "Extracted content from source."
        self.mock_analysis.is_pdf_file.return_value = False
        
        self.mock_follow_up_analysis.real_ai_analyse_fortext.return_value = "Follow-up analysis result"
        self.mock_follow_up_analysis.analyze_text.return_value = AnalysisOutcome(content="Follow-up analysis result")
        self.mock_follow_up_analysis.AnalysisFailure = AnalysisFailure
    
    def tearDown(self):
        """Clean up after tests."""
        self.analysis_patcher.stop()
        self.follow_up_analysis_patcher.stop()
    
    def test_init(self):
        """Test ResultsProcessor initialization."""
        processor = ResultsProcessor()
        
        self.assertIsNotNone(processor.data_extractor)
        self.assertIsNotNone(processor.chart_generator)
        self.assertEqual(len(processor.history), 0)
        self.assertIsNone(processor.current_result)
    
    def test_process_analysis_result_basic(self):
        """Test basic processing of analysis results."""
        raw_result = "This is a test result with 50% success rate and €500 budget."
        source_path = "test.txt"
        
        result = self.processor.process_analysis_result(
            raw_result=raw_result,
            source_path=source_path,
            analysis_type="test_analysis"
        )
        
        # Check basic properties
        self.assertIsInstance(result, ProcessedResult)
        self.assertEqual(result.content, raw_result)
        self.assertEqual(result.metadata.analysis_type, "test_analysis")
        self.assertEqual(result.metadata.model_used, "gpt-4o")
        self.assertIsNotNone(result.source_info)
        
        # Check that result is stored in history
        self.assertEqual(len(self.processor.history), 1)
        self.assertEqual(self.processor.current_result, result)
    
    def test_process_analysis_outcome_rejects_failure(self):
        outcome = AnalysisOutcome(error=AnalysisError(
            AnalysisErrorCode.CONNECTION_FAILED,
            "Nicht erreichbar",
            retryable=True
        ))
        with self.assertRaises(AnalysisFailure):
            self.processor.process_analysis_outcome(outcome, "test.txt", "test_analysis")
        self.assertEqual(self.processor.history, [])
        self.assertIsNone(self.processor.current_result)

    def test_process_analysis_outcome_accepts_success(self):
        outcome = AnalysisOutcome(content="Erfolgreiches Ergebnis", prompt_tokens=12, completion_tokens=8)
        result = self.processor.process_analysis_outcome(outcome, "test.txt", "test_analysis")
        self.assertEqual(result.content, "Erfolgreiches Ergebnis")
        self.assertEqual(result.metadata.tokens_used, 20)

    def test_process_analysis_result_with_data_extraction(self):
        """Test processing with data extraction."""
        raw_result = "Analysis shows 25% improvement, €1,000 budget, and John Doe as project manager."
        source_path = "test.txt"
        
        result = self.processor.process_analysis_result(
            raw_result=raw_result,
            source_path=source_path
        )
        
        # Check that structured data was extracted
        self.assertIsInstance(result.extracted_data, StructuredData)
        
        # Should have extracted numeric values (25%, €1,000)
        self.assertGreater(len(result.extracted_data.numeric_values), 0)
        
        # Should have follow-up actions
        self.assertGreater(len(result.follow_up_actions), 0)
    
    def test_analyze_text_enhanced(self):
        """Test enhanced text analysis."""
        text = "Analyze this text content."
        source_path = "input.txt"
        
        result = self.processor.analyze_text_enhanced(text, source_path)
        
        # Check that analysis function was called
        self.mock_analysis.real_ai_analyse_fortext.assert_called_once_with(text)
        
        # Check result properties
        self.assertIsInstance(result, ProcessedResult)
        self.assertEqual(result.metadata.analysis_type, "text_analysis")
        self.assertEqual(result.source_info.file_path, source_path)
    
    def test_analyze_pdf_enhanced(self):
        """Test enhanced PDF analysis."""
        pdf_path = "test.pdf"
        prompt = "Analyze this PDF"
        
        result = self.processor.analyze_pdf_enhanced(pdf_path, prompt)
        
        # Check that PDF analysis function was called
        self.mock_analysis.real_ai_analyse_forpdf.assert_called_once_with(pdf_path, prompt)
        
        # Check result properties
        self.assertIsInstance(result, ProcessedResult)
        self.assertEqual(result.metadata.analysis_type, "pdf_analysis")
        self.assertEqual(result.source_info.file_path, pdf_path)
    
    def test_analyze_content_enhanced_text_file(self):
        """Test enhanced content analysis for text files."""
        file_path = "test.txt"
        
        result = self.processor.analyze_content_enhanced(file_path)
        
        # Check that content extraction was called
        self.mock_analysis.text_extraction_youtube_website.assert_called_once_with(file_path)
        
        # Check that text analysis was performed
        self.mock_analysis.real_ai_analyse_fortext.assert_called()
        
        self.assertIsInstance(result, ProcessedResult)
    
    def test_analyze_content_enhanced_pdf_file(self):
        """Test enhanced content analysis for PDF files."""
        file_path = "test.pdf"
        self.mock_analysis.is_pdf_file.return_value = True
        
        result = self.processor.analyze_content_enhanced(file_path)
        
        # Check that PDF analysis was performed
        self.mock_analysis.real_ai_analyse_forpdf.assert_called()
        
        self.assertIsInstance(result, ProcessedResult)
    
    def test_analyze_content_enhanced_error_handling(self):
        """Test error handling in content analysis."""
        file_path = "nonexistent.txt"
        self.mock_analysis.text_extraction_youtube_website.return_value = "Fehler: Datei konnte nicht gefunden werden"
        
        result = self.processor.analyze_content_enhanced(file_path)
        
        # Should return error result
        self.assertIsInstance(result, ProcessedResult)
        self.assertEqual(result.metadata.analysis_type, "error")
        self.assertTrue(result.content.startswith("Fehler:"))
    
    def test_execute_follow_up_action_summarize(self):
        """Test executing summarize follow-up action."""
        # Create original result
        original_result = ProcessedResult(
            content="Original analysis content with detailed information.",
            source_info=SourceInfo(type="text", file_path="test.txt"),
            metadata=self._create_test_metadata()
        )
        
        # Execute follow-up action
        follow_up_result = self.processor.execute_follow_up_action(
            original_result, 
            ActionType.SUMMARIZE
        )
        
        # Check that analysis was called (the exact prompt may vary due to follow-up system)
        self.mock_follow_up_analysis.real_ai_analyse_fortext.assert_called()
        
        # Check result properties
        self.assertIsInstance(follow_up_result, ProcessedResult)
        self.assertIn("follow_up", follow_up_result.metadata.analysis_type)
        self.assertIn(f"follow_up_from_{original_result.id}", follow_up_result.metadata.tags)
    
    def test_execute_follow_up_action_deepen(self):
        """Test executing deepen follow-up action."""
        original_result = ProcessedResult(
            content="Original content",
            source_info=SourceInfo(type="text", file_path="test.txt"),
            metadata=self._create_test_metadata()
        )
        
        follow_up_result = self.processor.execute_follow_up_action(
            original_result, 
            ActionType.DEEPEN
        )
        
        # Check that analysis was called (the exact prompt may vary due to follow-up system)
        self.mock_follow_up_analysis.real_ai_analyse_fortext.assert_called()
        
        self.assertIn("follow_up", follow_up_result.metadata.analysis_type)
    
    def test_execute_follow_up_action_translate(self):
        """Test executing translate follow-up action."""
        original_result = ProcessedResult(
            content="German content to translate",
            source_info=SourceInfo(type="text", file_path="test.txt"),
            metadata=self._create_test_metadata()
        )
        
        follow_up_result = self.processor.execute_follow_up_action(
            original_result, 
            ActionType.TRANSLATE,
            parameters={'target_language': 'French'}
        )
        
        # Check that analysis was called (the exact prompt may vary due to follow-up system)
        self.mock_follow_up_analysis.real_ai_analyse_fortext.assert_called()
        
        self.assertIn("follow_up", follow_up_result.metadata.analysis_type)
    
    def test_get_action_suggestions_basic(self):
        """Test getting basic action suggestions."""
        result = ProcessedResult(
            content="Short content",
            metadata=self._create_test_metadata()
        )
        
        suggestions = self.processor.get_action_suggestions(result)
        
        # Should include default actions
        action_types = [action.action_type for action in suggestions]
        self.assertIn(ActionType.SUMMARIZE, action_types)
        self.assertIn(ActionType.DEEPEN, action_types)
        self.assertIn(ActionType.TRANSLATE, action_types)
    
    def test_get_action_suggestions_with_data(self):
        """Test action suggestions with extractable data."""
        # Create result with structured data
        structured_data = StructuredData()
        structured_data.numeric_values = [
            NumericValue(value=100, unit="€", value_type="currency")
        ]
        structured_data.tables = [
            DataTable(headers=["Name", "Value"], rows=[["Test", "123"]])
        ]
        
        result = ProcessedResult(
            content="Content with data",
            extracted_data=structured_data,
            metadata=self._create_test_metadata()
        )
        
        suggestions = self.processor.get_action_suggestions(result)
        
        # Should include data-specific actions
        action_types = [action.action_type for action in suggestions]
        self.assertIn(ActionType.VISUALIZE, action_types)
        self.assertIn(ActionType.EXPORT, action_types)
    
    def test_get_action_suggestions_long_content(self):
        """Test action suggestions for long content."""
        long_content = "This is a very long content. " * 100  # > 1000 characters
        
        result = ProcessedResult(
            content=long_content,
            metadata=self._create_test_metadata()
        )
        
        suggestions = self.processor.get_action_suggestions(result)
        
        # Should include short summary action
        short_summary_actions = [
            action for action in suggestions 
            if action.label == "Kurzzusammenfassung"
        ]
        self.assertGreater(len(short_summary_actions), 0)
    
    def test_get_visualization_suggestions(self):
        """Test getting visualization suggestions."""
        # Create result with visualizable data
        structured_data = StructuredData()
        structured_data.numeric_values = [
            NumericValue(value=100, unit="€", value_type="currency"),
            NumericValue(value=25, unit="%", value_type="percentage")
        ]
        
        result = ProcessedResult(
            content="Content with numeric data",
            extracted_data=structured_data,
            metadata=self._create_test_metadata()
        )
        
        suggestions = self.processor.get_visualization_suggestions(result)
        
        # Should return visualization suggestions
        self.assertIsInstance(suggestions, list)
        if suggestions:  # If chart generator returns suggestions
            self.assertIn('type', suggestions[0])
            self.assertIn('description', suggestions[0])
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation."""
        # Create structured data with various elements
        structured_data = StructuredData()
        structured_data.entities = [
            NamedEntity(text="John Doe", entity_type=EntityType.PERSON, confidence=0.9),
            NamedEntity(text="Berlin", entity_type=EntityType.LOCATION, confidence=0.8)
        ]
        structured_data.numeric_values = [
            NumericValue(value=100, unit="€", value_type="currency")
        ]
        structured_data.tables = [
            DataTable(headers=["Name"], rows=[["Test"]])
        ]
        
        score = self.processor._calculate_confidence_score(structured_data)
        
        # Should return a score between 0 and 1
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        
        # Should be relatively high given the good data
        self.assertGreater(score, 0.5)
    
    def test_history_management(self):
        """Test history management functions."""
        # Initially empty
        self.assertEqual(len(self.processor.get_history()), 0)
        self.assertIsNone(self.processor.get_current_result())
        
        # Add a result
        result = self.processor.analyze_text_enhanced("test", "test.txt")
        
        # Check history
        history = self.processor.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(self.processor.get_current_result(), result)
        
        # Clear history
        self.processor.clear_history()
        self.assertEqual(len(self.processor.get_history()), 0)
        self.assertIsNone(self.processor.get_current_result())
    
    def _create_test_metadata(self):
        """Helper to create test metadata."""
        from data_models import ResultMetadata
        return ResultMetadata(analysis_type="test")


class TestIntegrationFunctions(unittest.TestCase):
    """Test cases for integration functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the analysis functions
        self.analysis_patcher = patch('results_processor.analysis')
        self.mock_analysis = self.analysis_patcher.start()
        self.mock_analysis.real_ai_analyse_fortext.return_value = "Test result"
        self.mock_analysis.real_ai_analyse_forpdf.return_value = "PDF result"
        self.mock_analysis.text_extraction_youtube_website.return_value = "Extracted content"
        self.mock_analysis.is_pdf_file.return_value = False
    
    def tearDown(self):
        """Clean up after tests."""
        self.analysis_patcher.stop()
    
    def test_enhanced_analyze_text(self):
        """Test enhanced_analyze_text integration function."""
        result = enhanced_analyze_text("Test text", "source.txt")
        
        self.assertIsInstance(result, ProcessedResult)
        self.assertEqual(result.metadata.analysis_type, "text_analysis")
        self.mock_analysis.real_ai_analyse_fortext.assert_called_once_with("Test text")
    
    def test_enhanced_analyze_pdf(self):
        """Test enhanced_analyze_pdf integration function."""
        result = enhanced_analyze_pdf("test.pdf", "Analyze this")
        
        self.assertIsInstance(result, ProcessedResult)
        self.assertEqual(result.metadata.analysis_type, "pdf_analysis")
        self.mock_analysis.real_ai_analyse_forpdf.assert_called_once_with("test.pdf", "Analyze this")
    
    def test_enhanced_analyze_content(self):
        """Test enhanced_analyze_content integration function."""
        result = enhanced_analyze_content("test.txt")
        
        self.assertIsInstance(result, ProcessedResult)
        self.mock_analysis.text_extraction_youtube_website.assert_called_once_with("test.txt")
    
    def test_create_results_processor(self):
        """Test create_results_processor factory function."""
        processor = create_results_processor()
        
        self.assertIsInstance(processor, ResultsProcessor)
        self.assertIsNotNone(processor.data_extractor)
        self.assertIsNotNone(processor.chart_generator)


class TestResultsProcessorIntegration(unittest.TestCase):
    """Integration tests for ResultsProcessor with real components."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.processor = ResultsProcessor()
        
        # Mock only the OpenAI API calls to avoid actual API usage
        self.openai_patcher = patch('analysis.OpenAI')
        self.mock_openai_class = self.openai_patcher.start()
        
        # Set up mock OpenAI client
        self.mock_client = Mock()
        self.mock_openai_class.return_value = self.mock_client
        
        # Mock the completion response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test analysis result with 25% improvement and €1,000 budget. John Doe is the project manager."
        self.mock_client.chat.completions.create.return_value = mock_response
    
    def tearDown(self):
        """Clean up integration tests."""
        self.openai_patcher.stop()
    
    @patch('analysis.get_api_key')
    def test_full_integration_text_analysis(self, mock_get_api_key):
        """Test full integration with text analysis."""
        mock_get_api_key.return_value = "test-api-key"
        
        # Test with real text content
        text = "Analyze the quarterly report showing 25% growth and €50,000 revenue increase."
        
        result = self.processor.analyze_text_enhanced(text, "quarterly_report.txt")
        
        # Verify the result structure
        self.assertIsInstance(result, ProcessedResult)
        self.assertIsNotNone(result.content)
        self.assertIsNotNone(result.extracted_data)
        self.assertGreater(len(result.follow_up_actions), 0)
        
        # Verify that data extraction worked
        self.assertIsInstance(result.extracted_data, StructuredData)
        
        # Verify API was called
        self.mock_client.chat.completions.create.assert_called_once()
    
    @patch('analysis.get_api_key')
    def test_follow_up_action_integration(self, mock_get_api_key):
        """Test follow-up action execution integration."""
        mock_get_api_key.return_value = "test-api-key"
        
        # Create initial result
        original_result = self.processor.analyze_text_enhanced(
            "Initial analysis content", 
            "test.txt"
        )
        
        # Execute follow-up action
        follow_up_result = self.processor.execute_follow_up_action(
            original_result, 
            ActionType.SUMMARIZE
        )
        
        # Verify follow-up result
        self.assertIsInstance(follow_up_result, ProcessedResult)
        self.assertIn("follow_up", follow_up_result.metadata.analysis_type)
        self.assertIn(f"follow_up_from_{original_result.id}", follow_up_result.metadata.tags)
        
        # Verify both results are in history
        self.assertEqual(len(self.processor.history), 2)


if __name__ == '__main__':
    unittest.main()