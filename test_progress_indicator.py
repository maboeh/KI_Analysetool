"""
Tests for progress indication and status feedback system.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
import threading
import time
from datetime import datetime, timedelta

from progress_indicator import (
    ProgressIndicator, StatusFeedback, ProgressManager, ProgressStep,
    OperationType, ProgressStatus, ProgressInfo, global_progress_manager,
    with_progress
)


class TestProgressIndicator(unittest.TestCase):
    """Test progress indicator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
        self.progress_indicator = ProgressIndicator(self.root, show_details=True)
        
        self.test_steps = [
            ProgressStep("Step 1", "First step", weight=1.0),
            ProgressStep("Step 2", "Second step", weight=2.0),
            ProgressStep("Step 3", "Third step", weight=1.0)
        ]
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
    
    def test_progress_indicator_initialization(self):
        """Test progress indicator initializes correctly."""
        self.assertIsNotNone(self.progress_indicator.progress_frame)
        self.assertIsNotNone(self.progress_indicator.progress_bar)
        self.assertIsNotNone(self.progress_indicator.status_label)
        self.assertFalse(self.progress_indicator.is_visible)
    
    def test_start_operation(self):
        """Test starting a progress operation."""
        self.progress_indicator.start_operation(
            OperationType.FILE_PROCESSING,
            "Test Operation",
            self.test_steps
        )
        
        self.assertTrue(self.progress_indicator.is_visible)
        self.assertIsNotNone(self.progress_indicator.current_progress)
        self.assertEqual(
            self.progress_indicator.current_progress.operation_type,
            OperationType.FILE_PROCESSING
        )
        self.assertEqual(
            self.progress_indicator.current_progress.total_steps,
            len(self.test_steps)
        )
    
    def test_update_progress(self):
        """Test updating progress."""
        self.progress_indicator.start_operation(
            OperationType.FILE_PROCESSING,
            "Test Operation",
            self.test_steps
        )
        
        # Update to step 1
        self.progress_indicator.update_progress(1, "Processing step 1")
        
        self.assertEqual(self.progress_indicator.current_progress.current_step, 1)
        self.assertEqual(self.progress_indicator.current_progress.message, "Processing step 1")
        self.assertGreater(self.progress_indicator.current_progress.progress_percentage, 0)
    
    def test_complete_step(self):
        """Test completing individual steps."""
        self.progress_indicator.start_operation(
            OperationType.FILE_PROCESSING,
            "Test Operation",
            self.test_steps
        )
        
        # Complete first step
        self.progress_indicator.complete_step(0, "Step 1 completed")
        
        self.assertTrue(self.progress_indicator.current_progress.steps[0].completed)
        self.assertEqual(self.progress_indicator.current_progress.current_step, 1)
    
    def test_set_step_error(self):
        """Test setting step error."""
        self.progress_indicator.start_operation(
            OperationType.FILE_PROCESSING,
            "Test Operation",
            self.test_steps
        )
        
        # Set error on step 1
        self.progress_indicator.set_step_error(1, "Test error")
        
        self.assertEqual(self.progress_indicator.current_progress.steps[1].error, "Test error")
        self.assertEqual(self.progress_indicator.current_progress.status, ProgressStatus.ERROR)
    
    def test_complete_operation(self):
        """Test completing an operation."""
        self.progress_indicator.start_operation(
            OperationType.FILE_PROCESSING,
            "Test Operation",
            self.test_steps
        )
        
        self.progress_indicator.complete_operation("Operation successful")
        
        self.assertEqual(self.progress_indicator.current_progress.status, ProgressStatus.COMPLETED)
        self.assertEqual(self.progress_indicator.current_progress.progress_percentage, 100.0)
    
    def test_cancel_operation(self):
        """Test cancelling an operation."""
        cancel_called = False
        
        def cancel_callback():
            nonlocal cancel_called
            cancel_called = True
        
        self.progress_indicator.start_operation(
            OperationType.FILE_PROCESSING,
            "Test Operation",
            self.test_steps,
            cancel_callback
        )
        
        self.progress_indicator.cancel_operation("Operation cancelled")
        
        self.assertEqual(self.progress_indicator.current_progress.status, ProgressStatus.CANCELLED)
        self.assertTrue(cancel_called)
    
    def test_progress_calculation_with_weights(self):
        """Test progress calculation considers step weights."""
        self.progress_indicator.start_operation(
            OperationType.FILE_PROCESSING,
            "Test Operation",
            self.test_steps
        )
        
        # Complete first step (weight 1.0 out of total 4.0)
        self.progress_indicator.complete_step(0)
        
        expected_progress = (1.0 / 4.0) * 100  # 25%
        self.assertAlmostEqual(
            self.progress_indicator.current_progress.progress_percentage,
            expected_progress,
            places=1
        )
    
    def test_time_estimation(self):
        """Test time estimation functionality."""
        self.progress_indicator.start_operation(
            OperationType.FILE_PROCESSING,
            "Test Operation",
            self.test_steps
        )
        
        # Simulate some progress with time passage
        self.progress_indicator.current_progress.start_time = datetime.now() - timedelta(seconds=10)
        self.progress_indicator.update_progress(1, progress_percentage=25.0)
        
        # Should have estimated time remaining
        self.assertIsNotNone(self.progress_indicator.current_progress.estimated_time_remaining)


class TestStatusFeedback(unittest.TestCase):
    """Test status feedback functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
        self.status_feedback = StatusFeedback(self.root)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
    
    def test_status_feedback_initialization(self):
        """Test status feedback initializes correctly."""
        self.assertIsNotNone(self.status_feedback.status_label)
        self.assertEqual(self.status_feedback.status_var.get(), "Bereit")
    
    def test_show_status_message(self):
        """Test showing status messages."""
        self.status_feedback.show_status("Test message", color='blue')
        
        self.assertEqual(self.status_feedback.status_var.get(), "Test message")
        self.assertEqual(self.status_feedback.status_label.cget('fg'), 'blue')
    
    def test_show_success_message(self):
        """Test showing success messages."""
        self.status_feedback.show_success("Operation successful")
        
        self.assertIn("✓", self.status_feedback.status_var.get())
        self.assertEqual(self.status_feedback.status_label.cget('fg'), 'green')
    
    def test_show_error_message(self):
        """Test showing error messages."""
        self.status_feedback.show_error("Operation failed")
        
        self.assertIn("❌", self.status_feedback.status_var.get())
        self.assertEqual(self.status_feedback.status_label.cget('fg'), 'red')
    
    def test_show_warning_message(self):
        """Test showing warning messages."""
        self.status_feedback.show_warning("Warning message")
        
        self.assertIn("⚠️", self.status_feedback.status_var.get())
        self.assertEqual(self.status_feedback.status_label.cget('fg'), 'orange')
    
    def test_show_info_message(self):
        """Test showing info messages."""
        self.status_feedback.show_info("Info message")
        
        self.assertIn("ℹ️", self.status_feedback.status_var.get())
        self.assertEqual(self.status_feedback.status_label.cget('fg'), 'blue')


class TestProgressManager(unittest.TestCase):
    """Test progress manager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
        self.progress_manager = ProgressManager()
        
        # Create mock indicators and status feedback
        self.mock_indicator = Mock(spec=ProgressIndicator)
        self.mock_status = Mock(spec=StatusFeedback)
        
        self.progress_manager.register_indicator("test_indicator", self.mock_indicator)
        self.progress_manager.register_status_feedback("test_status", self.mock_status)
        
        self.test_steps = [
            ProgressStep("Step 1", "First step"),
            ProgressStep("Step 2", "Second step")
        ]
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
    
    def test_register_components(self):
        """Test registering indicators and status feedback."""
        self.assertIn("test_indicator", self.progress_manager.indicators)
        self.assertIn("test_status", self.progress_manager.status_feedbacks)
    
    def test_start_operation_through_manager(self):
        """Test starting operation through manager."""
        operation_id = self.progress_manager.start_operation(
            "test_indicator",
            OperationType.FILE_PROCESSING,
            "Test Operation",
            self.test_steps
        )
        
        self.assertIsNotNone(operation_id)
        self.mock_indicator.start_operation.assert_called_once()
        self.assertIn(operation_id, self.progress_manager.active_operations)
    
    def test_update_operation_through_manager(self):
        """Test updating operation through manager."""
        operation_id = self.progress_manager.start_operation(
            "test_indicator",
            OperationType.FILE_PROCESSING,
            "Test Operation",
            self.test_steps
        )
        
        self.progress_manager.update_operation(operation_id, 1, "Test message")
        
        self.mock_indicator.update_progress.assert_called_with(1, "Test message", None)
    
    def test_complete_operation_through_manager(self):
        """Test completing operation through manager."""
        operation_id = self.progress_manager.start_operation(
            "test_indicator",
            OperationType.FILE_PROCESSING,
            "Test Operation",
            self.test_steps
        )
        
        self.progress_manager.complete_operation(operation_id, "Success")
        
        self.mock_indicator.complete_operation.assert_called_with("Success")
        self.assertNotIn(operation_id, self.progress_manager.active_operations)
    
    def test_show_status_through_manager(self):
        """Test showing status through manager."""
        self.progress_manager.show_status("test_status", "Test message", "success")
        
        self.mock_status.show_success.assert_called_with("Test message", 3000)
    
    def test_handle_unknown_indicator(self):
        """Test handling unknown indicator gracefully."""
        operation_id = self.progress_manager.start_operation(
            "unknown_indicator",
            OperationType.FILE_PROCESSING,
            "Test Operation",
            self.test_steps
        )
        
        self.assertEqual(operation_id, "")  # Should return empty string
    
    def test_handle_unknown_status_feedback(self):
        """Test handling unknown status feedback gracefully."""
        # Should not raise exception
        self.progress_manager.show_status("unknown_status", "Test message")


class TestProgressDecorator(unittest.TestCase):
    """Test progress decorator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
        # Mock the global progress manager
        self.mock_manager = Mock(spec=ProgressManager)
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
    
    @patch('progress_indicator.global_progress_manager')
    def test_progress_decorator(self, mock_global_manager):
        """Test progress decorator functionality."""
        mock_global_manager.start_operation.return_value = "test_op_id"
        
        @with_progress(
            "test_indicator",
            OperationType.FILE_PROCESSING,
            "Test Operation",
            ["Step 1", "Step 2"]
        )
        def test_function(progress_callback=None):
            if progress_callback:
                progress_callback(0, "Starting")
                progress_callback(1, "Processing")
            return "result"
        
        result = test_function()
        
        self.assertEqual(result, "result")
        mock_global_manager.start_operation.assert_called_once()
        mock_global_manager.complete_operation.assert_called_once()
    
    @patch('progress_indicator.global_progress_manager')
    def test_progress_decorator_with_exception(self, mock_global_manager):
        """Test progress decorator handles exceptions."""
        mock_global_manager.start_operation.return_value = "test_op_id"
        
        @with_progress(
            "test_indicator",
            OperationType.FILE_PROCESSING,
            "Test Operation",
            ["Step 1", "Step 2"]
        )
        def failing_function(progress_callback=None):
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            failing_function()
        
        mock_global_manager.show_status.assert_called_once()


class TestProgressIntegration(unittest.TestCase):
    """Test integration scenarios for progress indication."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
    
    def test_multiple_concurrent_operations(self):
        """Test handling multiple concurrent operations."""
        manager = ProgressManager()
        
        # Create multiple indicators
        indicator1 = ProgressIndicator(self.root)
        indicator2 = ProgressIndicator(self.root)
        
        manager.register_indicator("op1", indicator1)
        manager.register_indicator("op2", indicator2)
        
        # Start multiple operations
        op1_id = manager.start_operation(
            "op1", OperationType.FILE_PROCESSING, "Operation 1",
            [ProgressStep("Step 1", "Description")]
        )
        
        op2_id = manager.start_operation(
            "op2", OperationType.CHART_GENERATION, "Operation 2",
            [ProgressStep("Step 1", "Description")]
        )
        
        # Both should be active
        active_ops = manager.get_active_operations()
        self.assertEqual(len(active_ops), 2)
        self.assertIn(op1_id, active_ops)
        self.assertIn(op2_id, active_ops)
    
    def test_progress_with_file_processing_simulation(self):
        """Test progress indication with simulated file processing."""
        indicator = ProgressIndicator(self.root, show_details=True)
        
        steps = [
            ProgressStep("Reading file", "Loading file content", weight=1.0),
            ProgressStep("Processing data", "Analyzing content", weight=3.0),
            ProgressStep("Generating output", "Creating results", weight=1.0)
        ]
        
        # Start operation
        indicator.start_operation(
            OperationType.FILE_PROCESSING,
            "Processing large file",
            steps
        )
        
        # Simulate processing steps
        indicator.update_progress(0, "Reading file...")
        self.assertEqual(indicator.current_progress.current_step, 0)
        
        indicator.complete_step(0, "File loaded successfully")
        self.assertTrue(indicator.current_progress.steps[0].completed)
        
        indicator.update_progress(1, "Processing data...")
        indicator.complete_step(1, "Data processed")
        
        indicator.update_progress(2, "Generating output...")
        indicator.complete_step(2, "Output generated")
        
        indicator.complete_operation("File processing completed successfully")
        
        self.assertEqual(indicator.current_progress.status, ProgressStatus.COMPLETED)
        self.assertEqual(indicator.current_progress.progress_percentage, 100.0)
    
    def test_error_handling_in_progress(self):
        """Test error handling during progress operations."""
        indicator = ProgressIndicator(self.root)
        
        steps = [
            ProgressStep("Step 1", "First step"),
            ProgressStep("Step 2", "Second step"),
            ProgressStep("Step 3", "Third step")
        ]
        
        indicator.start_operation(
            OperationType.FILE_PROCESSING,
            "Test Operation",
            steps
        )
        
        # Complete first step
        indicator.complete_step(0)
        
        # Error on second step
        indicator.set_step_error(1, "Processing failed")
        
        self.assertEqual(indicator.current_progress.status, ProgressStatus.ERROR)
        self.assertEqual(indicator.current_progress.steps[1].error, "Processing failed")
        
        # First step should still be completed
        self.assertTrue(indicator.current_progress.steps[0].completed)
        
        # Third step should not be affected
        self.assertFalse(indicator.current_progress.steps[2].completed)
        self.assertIsNone(indicator.current_progress.steps[2].error)


if __name__ == '__main__':
    # Run tests without showing Tkinter windows
    unittest.main()