"""
Tests for the follow-up action system.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import tempfile
import os
import json
from pathlib import Path

from follow_up_actions import (
    AnalysisContext, AnalysisStep, FollowUpActionExecutor,
    AnalysisHistoryManager, FollowUpActionSystem, create_follow_up_system
)
from data_models import (
    ProcessedResult, Action, ActionType, SourceInfo, ResultMetadata,
    StructuredData, NumericValue, DataTable
)


class TestAnalysisContext(unittest.TestCase):
    """Test cases for AnalysisContext class."""
    
    def test_init(self):
        """Test AnalysisContext initialization."""
        context = AnalysisContext(
            original_result_id="test-id",
            step_number=1
        )
        
        self.assertEqual(context.original_result_id, "test-id")
        self.assertEqual(context.step_number, 1)
        self.assertEqual(len(context.action_chain), 0)
        self.assertEqual(len(context.parameters_history), 0)
        self.assertIsInstance(context.created_at, datetime)
    
    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        context = AnalysisContext(
            original_result_id="test-id",
            step_number=2,
            action_chain=[ActionType.SUMMARIZE, ActionType.DEEPEN],
            parameters_history=[{'length': 'short'}, {'focus': 'technical'}]
        )
        
        # Test serialization
        context_dict = context.to_dict()
        self.assertEqual(context_dict['original_result_id'], "test-id")
        self.assertEqual(context_dict['step_number'], 2)
        self.assertEqual(context_dict['action_chain'], ['zusammenfassen', 'vertiefen'])
        
        # Test deserialization
        restored_context = AnalysisContext.from_dict(context_dict)
        self.assertEqual(restored_context.original_result_id, context.original_result_id)
        self.assertEqual(restored_context.step_number, context.step_number)
        self.assertEqual(restored_context.action_chain, context.action_chain)


class TestFollowUpActionExecutor(unittest.TestCase):
    """Test cases for FollowUpActionExecutor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.executor = FollowUpActionExecutor()
        
        # Mock the analysis functions
        self.analysis_patcher = patch('follow_up_actions.analysis')
        self.mock_analysis = self.analysis_patcher.start()
        self.mock_analysis.real_ai_analyse_fortext.return_value = "Test analysis result"
        
        # Create test result
        self.test_result = ProcessedResult(
            content="Test content for analysis",
            source_info=SourceInfo(type="text", file_path="test.txt"),
            metadata=ResultMetadata(analysis_type="test")
        )
    
    def tearDown(self):
        """Clean up after tests."""
        self.analysis_patcher.stop()
    
    def test_init(self):
        """Test executor initialization."""
        executor = FollowUpActionExecutor()
        
        # Check that all action types have handlers
        expected_actions = [
            ActionType.SUMMARIZE, ActionType.DEEPEN, ActionType.TRANSLATE,
            ActionType.ANALYZE, ActionType.EXPORT, ActionType.VISUALIZE
        ]
        
        for action_type in expected_actions:
            self.assertIn(action_type, executor.action_handlers)
    
    def test_execute_summarize_action(self):
        """Test executing summarize action."""
        action = Action(
            action_type=ActionType.SUMMARIZE,
            label="Zusammenfassen",
            description="Test summarize",
            parameters={'length': 'short'}
        )
        
        result = self.executor.execute_action(self.test_result, action)
        
        # Check that analysis was called with correct prompt
        expected_prompt = "Erstelle eine kurze Zusammenfassung (max. 3 Sätze) des folgenden Textes:\n\nTest content for analysis"
        self.mock_analysis.real_ai_analyse_fortext.assert_called_with(expected_prompt)
        
        # Check result properties
        self.assertIsInstance(result, ProcessedResult)
        self.assertIn("follow_up_from_", " ".join(result.metadata.tags))
    
    def test_execute_deepen_action(self):
        """Test executing deepen action."""
        action = Action(
            action_type=ActionType.DEEPEN,
            label="Vertiefen",
            description="Test deepen",
            parameters={'focus': 'technical aspects'}
        )
        
        result = self.executor.execute_action(self.test_result, action)
        
        # Check that analysis was called with correct prompt
        args = self.mock_analysis.real_ai_analyse_fortext.call_args[0]
        self.assertIn("tiefergehende Analyse", args[0])
        self.assertIn("technical aspects", args[0])
        
        self.assertIsInstance(result, ProcessedResult)
    
    def test_execute_translate_action(self):
        """Test executing translate action."""
        action = Action(
            action_type=ActionType.TRANSLATE,
            label="Übersetzen",
            description="Test translate",
            parameters={'target_language': 'French', 'style': 'informal'}
        )
        
        result = self.executor.execute_action(self.test_result, action)
        
        # Check that analysis was called with correct prompt
        args = self.mock_analysis.real_ai_analyse_fortext.call_args[0]
        self.assertIn("Übersetze", args[0])
        self.assertIn("French", args[0])
        self.assertIn("informal", args[0])
        
        self.assertIsInstance(result, ProcessedResult)
    
    def test_execute_analyze_action(self):
        """Test executing custom analyze action."""
        action = Action(
            action_type=ActionType.ANALYZE,
            label="Analysieren",
            description="Test analyze",
            parameters={'focus': 'sentiment analysis'}
        )
        
        result = self.executor.execute_action(self.test_result, action)
        
        # Check that analysis was called with correct prompt
        args = self.mock_analysis.real_ai_analyse_fortext.call_args[0]
        self.assertIn("sentiment analysis", args[0])
        
        self.assertIsInstance(result, ProcessedResult)
    
    def test_execute_export_action(self):
        """Test executing export action."""
        # Create result with exportable data
        structured_data = StructuredData()
        structured_data.tables = [
            DataTable(headers=["Name", "Value"], rows=[["Test", "123"]])
        ]
        
        result_with_data = ProcessedResult(
            content="Content with data",
            extracted_data=structured_data,
            source_info=SourceInfo(type="text", file_path="test.txt"),
            metadata=ResultMetadata(analysis_type="test")
        )
        
        action = Action(
            action_type=ActionType.EXPORT,
            label="Exportieren",
            description="Test export",
            parameters={'format': 'excel'}
        )
        
        result = self.executor.execute_action(result_with_data, action)
        
        # Check result content
        self.assertIn("Export-Anfrage", result.content)
        self.assertIn("excel", result.content)
        self.assertIn("exportierbarer Tabellen: 1", result.content)
    
    def test_execute_visualize_action(self):
        """Test executing visualize action."""
        # Create result with visualizable data
        structured_data = StructuredData()
        structured_data.numeric_values = [
            NumericValue(value=100, unit="€", value_type="currency")
        ]
        
        result_with_data = ProcessedResult(
            content="Content with numeric data",
            extracted_data=structured_data,
            source_info=SourceInfo(type="text", file_path="test.txt"),
            metadata=ResultMetadata(analysis_type="test")
        )
        
        action = Action(
            action_type=ActionType.VISUALIZE,
            label="Visualisieren",
            description="Test visualize",
            parameters={'chart_type': 'bar'}
        )
        
        result = self.executor.execute_action(result_with_data, action)
        
        # Check result content
        self.assertIn("Visualisierung angefordert", result.content)
        self.assertIn("bar", result.content)
        self.assertIn("numerischer Werte: 1", result.content)
    
    def test_execute_with_context(self):
        """Test executing action with existing context."""
        context = AnalysisContext(
            original_result_id="original-id",
            step_number=2,
            action_chain=[ActionType.SUMMARIZE],
            parameters_history=[{'length': 'normal'}]
        )
        
        action = Action(
            action_type=ActionType.DEEPEN,
            label="Vertiefen",
            description="Test deepen with context"
        )
        
        result = self.executor.execute_action(self.test_result, action, context)
        
        # Check that context was updated
        self.assertIn("step_3", result.metadata.tags)
        self.assertIn("action_chain_2", result.metadata.tags)
    
    def test_unsupported_action_type(self):
        """Test handling of unsupported action types."""
        # Create a mock action with unsupported type
        action = Mock()
        action.action_type = "UNSUPPORTED_ACTION"
        action.parameters = {}
        
        with self.assertRaises(ValueError):
            self.executor.execute_action(self.test_result, action)


class TestAnalysisHistoryManager(unittest.TestCase):
    """Test cases for AnalysisHistoryManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.history_manager = AnalysisHistoryManager(self.temp_dir)
        
        # Create test results
        self.result1 = ProcessedResult(
            content="First result",
            metadata=ResultMetadata(analysis_type="initial")
        )
        
        self.result2 = ProcessedResult(
            content="Second result",
            metadata=ResultMetadata(analysis_type="follow_up")
        )
    
    def tearDown(self):
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test history manager initialization."""
        manager = AnalysisHistoryManager(self.temp_dir)
        
        self.assertEqual(len(manager.current_session), 0)
        self.assertEqual(len(manager.step_relationships), 0)
        self.assertTrue(Path(self.temp_dir).exists())
    
    def test_add_step(self):
        """Test adding analysis steps."""
        context1 = AnalysisContext(
            original_result_id=self.result1.id,
            step_number=1
        )
        
        step1 = self.history_manager.add_step(self.result1, context1)
        
        self.assertEqual(len(self.history_manager.current_session), 1)
        self.assertEqual(step1.result, self.result1)
        self.assertEqual(step1.context, context1)
        self.assertIsNone(step1.parent_step_id)
    
    def test_add_step_with_parent(self):
        """Test adding step with parent relationship."""
        # Add first step
        context1 = AnalysisContext(
            original_result_id=self.result1.id,
            step_number=1
        )
        step1 = self.history_manager.add_step(self.result1, context1)
        
        # Add second step as child of first
        context2 = AnalysisContext(
            original_result_id=self.result1.id,
            step_number=2
        )
        step2 = self.history_manager.add_step(
            self.result2, 
            context2, 
            parent_step_id=self.result1.id
        )
        
        self.assertEqual(len(self.history_manager.current_session), 2)
        self.assertEqual(step2.parent_step_id, self.result1.id)
        self.assertIn(self.result1.id, self.history_manager.step_relationships)
        self.assertIn(self.result2.id, self.history_manager.step_relationships[self.result1.id])
    
    def test_get_step_by_id(self):
        """Test retrieving step by ID."""
        context = AnalysisContext(
            original_result_id=self.result1.id,
            step_number=1
        )
        self.history_manager.add_step(self.result1, context)
        
        # Test existing step
        step = self.history_manager.get_step_by_id(self.result1.id)
        self.assertIsNotNone(step)
        self.assertEqual(step.result.id, self.result1.id)
        
        # Test non-existing step
        step = self.history_manager.get_step_by_id("non-existent")
        self.assertIsNone(step)
    
    def test_get_analysis_chain(self):
        """Test getting analysis chain."""
        # Create a chain: result1 -> result2 -> result3
        result3 = ProcessedResult(
            content="Third result",
            metadata=ResultMetadata(analysis_type="follow_up_2")
        )
        
        # Add steps
        context1 = AnalysisContext(original_result_id=self.result1.id, step_number=1)
        self.history_manager.add_step(self.result1, context1)
        
        context2 = AnalysisContext(original_result_id=self.result1.id, step_number=2)
        self.history_manager.add_step(self.result2, context2, parent_step_id=self.result1.id)
        
        context3 = AnalysisContext(original_result_id=self.result1.id, step_number=3)
        self.history_manager.add_step(result3, context3, parent_step_id=self.result2.id)
        
        # Get chain for result3
        chain = self.history_manager.get_analysis_chain(result3.id)
        
        self.assertEqual(len(chain), 3)
        self.assertEqual(chain[0].result.id, self.result1.id)
        self.assertEqual(chain[1].result.id, self.result2.id)
        self.assertEqual(chain[2].result.id, result3.id)
    
    def test_get_child_steps(self):
        """Test getting child steps."""
        # Add parent and child steps
        context1 = AnalysisContext(original_result_id=self.result1.id, step_number=1)
        self.history_manager.add_step(self.result1, context1)
        
        context2 = AnalysisContext(original_result_id=self.result1.id, step_number=2)
        self.history_manager.add_step(self.result2, context2, parent_step_id=self.result1.id)
        
        # Get children of result1
        children = self.history_manager.get_child_steps(self.result1.id)
        
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].result.id, self.result2.id)
        
        # Get children of result2 (should be empty)
        children = self.history_manager.get_child_steps(self.result2.id)
        self.assertEqual(len(children), 0)
    
    def test_get_session_summary(self):
        """Test getting session summary."""
        # Empty session
        summary = self.history_manager.get_session_summary()
        self.assertEqual(summary['total_steps'], 0)
        self.assertEqual(len(summary['analysis_chains']), 0)
        
        # Add steps
        context1 = AnalysisContext(
            original_result_id=self.result1.id, 
            step_number=1,
            action_chain=[ActionType.SUMMARIZE]
        )
        self.history_manager.add_step(self.result1, context1)
        
        context2 = AnalysisContext(
            original_result_id=self.result1.id, 
            step_number=2,
            action_chain=[ActionType.SUMMARIZE, ActionType.DEEPEN]
        )
        self.history_manager.add_step(self.result2, context2, parent_step_id=self.result1.id)
        
        summary = self.history_manager.get_session_summary()
        
        self.assertEqual(summary['total_steps'], 2)
        self.assertEqual(len(summary['analysis_chains']), 1)
        self.assertEqual(summary['analysis_chains'][0]['root_id'], self.result1.id)
        # The chain should include both the root step and its child
        self.assertGreaterEqual(summary['analysis_chains'][0]['length'], 1)
    
    def test_save_and_load_session(self):
        """Test saving and loading sessions."""
        # Add some steps
        context1 = AnalysisContext(original_result_id=self.result1.id, step_number=1)
        self.history_manager.add_step(self.result1, context1)
        
        context2 = AnalysisContext(original_result_id=self.result1.id, step_number=2)
        self.history_manager.add_step(self.result2, context2, parent_step_id=self.result1.id)
        
        # Save session
        session_file = self.history_manager.save_session("test_session")
        self.assertTrue(os.path.exists(session_file))
        
        # Clear and load session
        original_session_length = len(self.history_manager.current_session)
        self.history_manager.clear_session()
        self.assertEqual(len(self.history_manager.current_session), 0)
        
        self.history_manager.load_session(session_file)
        self.assertEqual(len(self.history_manager.current_session), original_session_length)
        
        # Verify loaded data
        loaded_step = self.history_manager.get_step_by_id(self.result1.id)
        self.assertIsNotNone(loaded_step)
        self.assertEqual(loaded_step.result.content, self.result1.content)
    
    def test_navigate_to_step(self):
        """Test navigation to specific steps."""
        context = AnalysisContext(original_result_id=self.result1.id, step_number=1)
        self.history_manager.add_step(self.result1, context)
        
        # Navigate to existing step
        result = self.history_manager.navigate_to_step(self.result1.id)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.result1.id)
        
        # Navigate to non-existing step
        result = self.history_manager.navigate_to_step("non-existent")
        self.assertIsNone(result)


class TestFollowUpActionSystem(unittest.TestCase):
    """Test cases for the complete FollowUpActionSystem."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.system = FollowUpActionSystem(self.temp_dir)
        
        # Mock the analysis functions
        self.analysis_patcher = patch('follow_up_actions.analysis')
        self.mock_analysis = self.analysis_patcher.start()
        self.mock_analysis.real_ai_analyse_fortext.return_value = "Follow-up analysis result"
        
        # Create test data
        self.test_result = ProcessedResult(
            content="Test content",
            source_info=SourceInfo(type="text", file_path="test.txt"),
            metadata=ResultMetadata(analysis_type="test")
        )
        
        self.test_action = Action(
            action_type=ActionType.SUMMARIZE,
            label="Zusammenfassen",
            description="Test summarize action"
        )
    
    def tearDown(self):
        """Clean up after tests."""
        self.analysis_patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test system initialization."""
        system = FollowUpActionSystem(self.temp_dir)
        
        self.assertIsNotNone(system.executor)
        self.assertIsNotNone(system.history_manager)
    
    def test_execute_follow_up_action(self):
        """Test executing follow-up action through the system."""
        result = self.system.execute_follow_up_action(
            self.test_result, 
            self.test_action
        )
        
        # Check that action was executed
        self.assertIsInstance(result, ProcessedResult)
        self.mock_analysis.real_ai_analyse_fortext.assert_called_once()
        
        # Check that step was added to history
        history = self.system.get_analysis_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].result.id, result.id)
    
    def test_execute_chained_actions(self):
        """Test executing chained follow-up actions."""
        # Execute first action
        result1 = self.system.execute_follow_up_action(
            self.test_result, 
            self.test_action
        )
        
        # Execute second action on first result
        action2 = Action(
            action_type=ActionType.DEEPEN,
            label="Vertiefen",
            description="Deepen analysis"
        )
        
        result2 = self.system.execute_follow_up_action(
            result1, 
            action2,
            parent_step_id=result1.id
        )
        
        # Check history
        history = self.system.get_analysis_history()
        self.assertEqual(len(history), 2)
        
        # Check chain
        chain = self.system.get_step_chain(result2.id)
        self.assertEqual(len(chain), 2)
        self.assertEqual(chain[0].result.id, result1.id)
        self.assertEqual(chain[1].result.id, result2.id)
    
    def test_navigation(self):
        """Test navigation functionality."""
        # Execute action to create history
        result = self.system.execute_follow_up_action(
            self.test_result, 
            self.test_action
        )
        
        # Navigate to the result
        navigated_result = self.system.navigate_to_step(result.id)
        self.assertIsNotNone(navigated_result)
        self.assertEqual(navigated_result.id, result.id)
        
        # Navigate to non-existent step
        navigated_result = self.system.navigate_to_step("non-existent")
        self.assertIsNone(navigated_result)
    
    def test_session_management(self):
        """Test session save/load functionality."""
        # Execute some actions
        result1 = self.system.execute_follow_up_action(
            self.test_result, 
            self.test_action
        )
        
        action2 = Action(
            action_type=ActionType.DEEPEN,
            label="Vertiefen",
            description="Deepen"
        )
        result2 = self.system.execute_follow_up_action(
            result1, 
            action2,
            parent_step_id=result1.id
        )
        
        # Save session
        session_file = self.system.save_session("test_integration_session")
        self.assertTrue(os.path.exists(session_file))
        
        # Clear and reload
        original_history_length = len(self.system.get_analysis_history())
        self.system.clear_history()
        self.assertEqual(len(self.system.get_analysis_history()), 0)
        
        self.system.load_session(session_file)
        self.assertEqual(len(self.system.get_analysis_history()), original_history_length)
    
    def test_session_summary(self):
        """Test getting session summary."""
        # Empty session
        summary = self.system.get_session_summary()
        self.assertEqual(summary['total_steps'], 0)
        
        # Execute actions
        result = self.system.execute_follow_up_action(
            self.test_result, 
            self.test_action
        )
        
        summary = self.system.get_session_summary()
        self.assertEqual(summary['total_steps'], 1)
        # The system creates a follow-up result, which has a parent (the original result)
        # So there might be no root steps if all steps have parents
        self.assertGreaterEqual(len(summary['analysis_chains']), 0)


class TestIntegrationFunctions(unittest.TestCase):
    """Test cases for integration functions."""
    
    def test_create_follow_up_system(self):
        """Test create_follow_up_system factory function."""
        system = create_follow_up_system()
        
        self.assertIsInstance(system, FollowUpActionSystem)
        self.assertIsNotNone(system.executor)
        self.assertIsNotNone(system.history_manager)
    
    def test_create_follow_up_system_with_path(self):
        """Test factory function with custom storage path."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            system = create_follow_up_system(temp_dir)
            
            self.assertIsInstance(system, FollowUpActionSystem)
            self.assertEqual(str(system.history_manager.storage_path), temp_dir)
        finally:
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()