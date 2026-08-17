"""
Unit tests for ActionButtonsFrame

Tests the interactive action buttons functionality including dynamic button generation,
action handlers, context menus, and content analysis.
"""

import unittest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from action_buttons import ActionButtonsFrame, ActionButton, ActionType


class TestActionButtonsFrame(unittest.TestCase):
    """Test cases for ActionButtonsFrame"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        
        # Mock callback function
        self.mock_callback = Mock()
        
        self.frame = ActionButtonsFrame(self.root, on_action_callback=self.mock_callback)
    
    def tearDown(self):
        """Clean up after tests"""
        self.root.destroy()
    
    def test_frame_initialization(self):
        """Test that the frame initializes correctly"""
        self.assertIsInstance(self.frame, ActionButtonsFrame)
        self.assertEqual(self.frame.current_content, "")
        self.assertEqual(self.frame.content_type, "text")
        self.assertEqual(len(self.frame.action_history), 0)
        self.assertGreater(len(self.frame.available_actions), 0)
        
        # Check that main components exist
        self.assertIsNotNone(self.frame.title_label)
        self.assertIsNotNone(self.frame.buttons_frame)
        self.assertIsNotNone(self.frame.more_actions_btn)
        self.assertIsNotNone(self.frame.history_btn)
    
    def test_default_actions_creation(self):
        """Test that default actions are created correctly"""
        action_types = [action.action_type for action in self.frame.available_actions]
        
        self.assertIn(ActionType.ZUSAMMENFASSEN, action_types)
        self.assertIn(ActionType.VERTIEFEN, action_types)
        self.assertIn(ActionType.UEBERSETZEN, action_types)
        self.assertIn(ActionType.ANALYSIEREN, action_types)
        
        # Check that all actions have required properties
        for action in self.frame.available_actions:
            self.assertIsNotNone(action.label)
            self.assertIsNotNone(action.description)
            self.assertIsNotNone(action.callback)
    
    def test_update_content_basic(self):
        """Test basic content update functionality"""
        test_content = "This is a test content for analysis."
        
        self.frame.update_content(test_content, "text")
        
        self.assertEqual(self.frame.current_content, test_content)
        self.assertEqual(self.frame.content_type, "text")
    
    def test_content_analysis_for_summarization(self):
        """Test content analysis for summarization action"""
        # Short content - should disable summarization
        short_content = "Short text"
        self.frame.update_content(short_content)
        
        summary_action = next((a for a in self.frame.available_actions 
                             if a.action_type == ActionType.ZUSAMMENFASSEN), None)
        self.assertIsNotNone(summary_action)
        self.assertFalse(summary_action.enabled)
        
        # Long content - should enable summarization
        long_content = "This is a much longer text content that should be long enough to warrant summarization. " * 10
        self.frame.update_content(long_content)
        
        summary_action = next((a for a in self.frame.available_actions 
                             if a.action_type == ActionType.ZUSAMMENFASSEN), None)
        self.assertIsNotNone(summary_action)
        self.assertTrue(summary_action.enabled)
    
    def test_expandable_topics_detection(self):
        """Test detection of expandable topics in content"""
        # Content with expandable keywords
        expandable_content = "This concept is interesting and the theory behind it needs more explanation."
        self.assertTrue(self.frame._has_expandable_topics(expandable_content))
        
        # Content without expandable keywords
        simple_content = "The weather is nice today."
        self.assertFalse(self.frame._has_expandable_topics(simple_content))
    
    def test_analyzable_content_detection(self):
        """Test detection of analyzable content"""
        # Content with numbers
        numeric_content = "Sales increased by 25% to reach 1000 units."
        self.assertTrue(self.frame._has_analyzable_content(numeric_content))
        
        # Content with dates
        date_content = "The meeting is scheduled for 15.12.2024."
        self.assertTrue(self.frame._has_analyzable_content(date_content))
        
        # Content with lists
        list_content = "Items:\n- First item\n- Second item"
        self.assertTrue(self.frame._has_analyzable_content(list_content))
        
        # Simple content without analyzable elements
        simple_content = "Hello world"
        self.assertFalse(self.frame._has_analyzable_content(simple_content))
    
    def test_numerical_data_detection(self):
        """Test detection of numerical data in content"""
        # Content with decimal numbers
        decimal_content = "The price is 19.99 and the discount is 15%."
        self.frame.update_content(decimal_content)
        self.assertTrue(self.frame._contains_numerical_data())
        
        # Content with currency
        currency_content = "The cost is €500 or $600."
        self.frame.update_content(currency_content)
        self.assertTrue(self.frame._contains_numerical_data())
        
        # Content without numerical data
        text_content = "This is just plain text without numbers."
        self.frame.update_content(text_content)
        self.assertFalse(self.frame._contains_numerical_data())
    
    def test_code_detection(self):
        """Test detection of code in content"""
        # Content with code blocks
        code_block_content = "Here's some code:\n```python\ndef hello():\n    print('Hello')\n```"
        self.frame.update_content(code_block_content)
        self.assertTrue(self.frame._contains_code())
        
        # Content with inline code
        inline_code_content = "Use the `print()` function to output text."
        self.frame.update_content(inline_code_content)
        self.assertTrue(self.frame._contains_code())
        
        # Content with function definitions
        function_content = "def calculate_sum(a, b):\n    return a + b"
        self.frame.update_content(function_content)
        self.assertTrue(self.frame._contains_code())
        
        # Content without code
        text_content = "This is just regular text content."
        self.frame.update_content(text_content)
        self.assertFalse(self.frame._contains_code())
    
    def test_references_detection(self):
        """Test detection of references in content"""
        # Content with numbered references
        ref_content = "According to the study [1], the results show improvement."
        self.frame.update_content(ref_content)
        self.assertTrue(self.frame._contains_references())
        
        # Content with URLs
        url_content = "More information at https://example.com"
        self.frame.update_content(url_content)
        self.assertTrue(self.frame._contains_references())
        
        # Content with DOI
        doi_content = "Published paper doi: 10.1000/182"
        self.frame.update_content(doi_content)
        self.assertTrue(self.frame._contains_references())
        
        # Content without references
        text_content = "This is just regular text content."
        self.frame.update_content(text_content)
        self.assertFalse(self.frame._contains_references())
    
    def test_dynamic_actions_addition(self):
        """Test that dynamic actions are added based on content"""
        # Content with numerical data should add data analysis action
        numeric_content = "Sales: 1000 units, Growth: 25%, Revenue: €50,000"
        self.frame.update_content(numeric_content)
        
        custom_actions = [a for a in self.frame.available_actions 
                         if a.action_type == ActionType.CUSTOM]
        action_labels = [a.label for a in custom_actions]
        
        self.assertIn("Daten analysieren", action_labels)
        
        # Content with code should add code explanation action
        code_content = "```python\ndef hello():\n    print('Hello World')\n```"
        self.frame.update_content(code_content)
        
        custom_actions = [a for a in self.frame.available_actions 
                         if a.action_type == ActionType.CUSTOM]
        action_labels = [a.label for a in custom_actions]
        
        self.assertIn("Code erklären", action_labels)
    
    def test_action_execution(self):
        """Test action execution with callback"""
        test_content = "Test content for action execution"
        self.frame.update_content(test_content)
        
        # Execute an action
        self.frame._execute_action("test_action")
        
        # Check that callback was called
        self.mock_callback.assert_called_once_with("test_action", test_content, "text")
    
    def test_action_history(self):
        """Test action history functionality"""
        initial_history_length = len(self.frame.action_history)
        
        # Execute some actions
        self.frame._add_to_history("test_action_1", "Test Action 1")
        self.frame._add_to_history("test_action_2", "Test Action 2")
        
        # Check history was updated
        self.assertEqual(len(self.frame.action_history), initial_history_length + 2)
        
        # Check history entries
        last_entry = self.frame.action_history[-1]
        self.assertEqual(last_entry["action_type"], "test_action_2")
        self.assertEqual(last_entry["action_label"], "Test Action 2")
        self.assertIsInstance(last_entry["timestamp"], datetime)
    
    def test_history_limit(self):
        """Test that action history is limited to 20 entries"""
        # Add more than 20 entries
        for i in range(25):
            self.frame._add_to_history(f"action_{i}", f"Action {i}")
        
        # Check that only 20 entries are kept
        self.assertEqual(len(self.frame.action_history), 20)
        
        # Check that the most recent entries are kept
        last_entry = self.frame.action_history[-1]
        self.assertEqual(last_entry["action_type"], "action_24")
    
    def test_clear_history(self):
        """Test clearing action history"""
        # Add some history entries
        self.frame._add_to_history("test_action", "Test Action")
        self.assertGreater(len(self.frame.action_history), 0)
        
        # Clear history
        self.frame.clear_history()
        self.assertEqual(len(self.frame.action_history), 0)
    
    def test_custom_action_management(self):
        """Test adding and removing custom actions"""
        initial_count = len(self.frame.available_actions)
        
        # Add custom action
        custom_action = ActionButton(
            action_type=ActionType.CUSTOM,
            label="Custom Test Action",
            description="A test custom action",
            callback=lambda: None
        )
        
        self.frame.add_custom_action(custom_action)
        self.assertEqual(len(self.frame.available_actions), initial_count + 1)
        
        # Check that the action was added
        action_labels = [a.label for a in self.frame.available_actions]
        self.assertIn("Custom Test Action", action_labels)
        
        # Remove the custom action
        self.frame.remove_action(ActionType.CUSTOM)
        
        # Check that custom actions were removed
        remaining_custom = [a for a in self.frame.available_actions 
                          if a.action_type == ActionType.CUSTOM]
        self.assertEqual(len(remaining_custom), 0)
    
    def test_action_enable_disable(self):
        """Test enabling and disabling specific actions"""
        # Find a default action
        summary_action = next((a for a in self.frame.available_actions 
                             if a.action_type == ActionType.ZUSAMMENFASSEN), None)
        self.assertIsNotNone(summary_action)
        
        # Disable the action
        self.frame.set_action_enabled(ActionType.ZUSAMMENFASSEN, False)
        self.assertFalse(summary_action.enabled)
        
        # Enable the action
        self.frame.set_action_enabled(ActionType.ZUSAMMENFASSEN, True)
        self.assertTrue(summary_action.enabled)
    
    def test_empty_content_handling(self):
        """Test handling of empty content"""
        self.frame.update_content("", "text")
        
        # All actions should be disabled for empty content
        for action in self.frame.available_actions:
            self.assertFalse(action.enabled)
    
    def test_action_button_dataclass(self):
        """Test ActionButton dataclass functionality"""
        action = ActionButton(
            action_type=ActionType.CUSTOM,
            label="Test Action",
            description="Test Description"
        )
        
        self.assertEqual(action.action_type, ActionType.CUSTOM)
        self.assertEqual(action.label, "Test Action")
        self.assertEqual(action.description, "Test Description")
        self.assertIsNone(action.icon)
        self.assertTrue(action.enabled)
        self.assertIsNone(action.callback)
        self.assertEqual(action.parameters, {})
    
    def test_action_button_with_parameters(self):
        """Test ActionButton with custom parameters"""
        test_params = {"param1": "value1", "param2": 42}
        
        action = ActionButton(
            action_type=ActionType.CUSTOM,
            label="Test Action",
            description="Test Description",
            parameters=test_params,
            enabled=False
        )
        
        self.assertEqual(action.parameters, test_params)
        self.assertFalse(action.enabled)


class TestActionType(unittest.TestCase):
    """Test cases for ActionType enum"""
    
    def test_action_type_values(self):
        """Test that ActionType enum has expected values"""
        expected_values = [
            "zusammenfassen", "vertiefen", "uebersetzen", 
            "analysieren", "exportieren", "visualisieren", 
            "vergleichen", "custom"
        ]
        
        actual_values = [action_type.value for action_type in ActionType]
        
        for expected in expected_values:
            self.assertIn(expected, actual_values)
    
    def test_action_type_enum_access(self):
        """Test accessing ActionType enum members"""
        self.assertEqual(ActionType.ZUSAMMENFASSEN.value, "zusammenfassen")
        self.assertEqual(ActionType.VERTIEFEN.value, "vertiefen")
        self.assertEqual(ActionType.UEBERSETZEN.value, "uebersetzen")
        self.assertEqual(ActionType.ANALYSIEREN.value, "analysieren")
        self.assertEqual(ActionType.CUSTOM.value, "custom")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)