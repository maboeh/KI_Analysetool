"""
Progress indication and status feedback system for long-running operations.

This module provides progress bars, status messages, and loading indicators
for file processing, analysis, chart generation, and export operations.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Optional, Callable, Any, Dict, List
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta


class OperationType(Enum):
    """Types of operations that can show progress."""
    FILE_PROCESSING = "file_processing"
    DATA_EXTRACTION = "data_extraction"
    CHART_GENERATION = "chart_generation"
    EXPORT = "export"
    OCR_PROCESSING = "ocr_processing"
    ANALYSIS = "analysis"
    MULTI_FILE = "multi_file"


class ProgressStatus(Enum):
    """Status of a progress operation."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class ProgressStep:
    """Represents a step in a multi-step operation."""
    name: str
    description: str
    weight: float = 1.0  # Relative weight for progress calculation
    completed: bool = False
    error: Optional[str] = None


@dataclass
class ProgressInfo:
    """Information about current progress."""
    operation_type: OperationType
    operation_name: str
    current_step: int
    total_steps: int
    progress_percentage: float
    status: ProgressStatus
    message: str
    estimated_time_remaining: Optional[timedelta] = None
    start_time: Optional[datetime] = None
    steps: List[ProgressStep] = None


class ProgressIndicator:
    """
    Main progress indicator widget that can be embedded in Tkinter applications.
    
    Provides progress bars, status messages, and estimated time remaining
    for long-running operations.
    """
    
    def __init__(self, parent_widget: tk.Widget, show_details: bool = True):
        """
        Initialize progress indicator.
        
        Args:
            parent_widget: Parent Tkinter widget
            show_details: Whether to show detailed step information
        """
        self.parent = parent_widget
        self.show_details = show_details
        self.logger = logging.getLogger(__name__)
        
        # Progress tracking
        self.current_progress: Optional[ProgressInfo] = None
        self.is_visible = False
        self.cancel_requested = False
        self.cancel_callback: Optional[Callable] = None
        
        # UI components
        self.progress_frame: Optional[tk.Frame] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.status_label: Optional[tk.Label] = None
        self.detail_label: Optional[tk.Label] = None
        self.time_label: Optional[tk.Label] = None
        self.cancel_button: Optional[tk.Button] = None
        self.step_listbox: Optional[tk.Listbox] = None
        
        # Animation
        self.animation_thread: Optional[threading.Thread] = None
        self.animation_running = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the progress indicator UI components."""
        # Main frame (initially hidden)
        self.progress_frame = tk.Frame(self.parent, relief=tk.RAISED, borderwidth=1)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(pady=(10, 5), padx=10, fill=tk.X)
        
        # Status message
        self.status_label = tk.Label(
            self.progress_frame,
            text="Bereit...",
            font=('Arial', 10, 'bold')
        )
        self.status_label.pack(pady=2)
        
        # Detail message
        self.detail_label = tk.Label(
            self.progress_frame,
            text="",
            font=('Arial', 9),
            fg='gray'
        )
        self.detail_label.pack(pady=2)
        
        # Time remaining
        self.time_label = tk.Label(
            self.progress_frame,
            text="",
            font=('Arial', 8),
            fg='blue'
        )
        self.time_label.pack(pady=2)
        
        # Control buttons frame
        button_frame = tk.Frame(self.progress_frame)
        button_frame.pack(pady=5)
        
        # Cancel button
        self.cancel_button = tk.Button(
            button_frame,
            text="Abbrechen",
            command=self._on_cancel_clicked,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Step details (if enabled)
        if self.show_details:
            details_frame = tk.LabelFrame(self.progress_frame, text="Schritte")
            details_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
            
            self.step_listbox = tk.Listbox(
                details_frame,
                height=4,
                font=('Arial', 8)
            )
            self.step_listbox.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)
            
            # Scrollbar for steps
            step_scrollbar = tk.Scrollbar(details_frame, orient=tk.VERTICAL)
            step_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.step_listbox.config(yscrollcommand=step_scrollbar.set)
            step_scrollbar.config(command=self.step_listbox.yview)
    
    def start_operation(self, operation_type: OperationType, operation_name: str,
                       steps: List[ProgressStep], cancel_callback: Optional[Callable] = None):
        """
        Start a new progress operation.
        
        Args:
            operation_type: Type of operation
            operation_name: Human-readable name of the operation
            steps: List of steps in the operation
            cancel_callback: Optional callback for cancellation
        """
        self.cancel_requested = False
        self.cancel_callback = cancel_callback
        
        self.current_progress = ProgressInfo(
            operation_type=operation_type,
            operation_name=operation_name,
            current_step=0,
            total_steps=len(steps),
            progress_percentage=0.0,
            status=ProgressStatus.IN_PROGRESS,
            message=f"{operation_name} wird gestartet...",
            start_time=datetime.now(),
            steps=steps
        )
        
        self._show_progress()
        self._update_display()
        
        # Enable cancel button if callback provided
        if cancel_callback:
            self.cancel_button.config(state=tk.NORMAL)
        
        # Start animation for indeterminate operations
        if operation_type in [OperationType.OCR_PROCESSING, OperationType.ANALYSIS]:
            self._start_animation()

    def start(self, message: str):
        self.start_operation(
            OperationType.ANALYSIS,
            message,
            [ProgressStep(name=message, description=message)]
        )

    def stop(self):
        if self.current_progress:
            self.current_progress.status = ProgressStatus.COMPLETED
            self.current_progress.progress_percentage = 100.0
        self._stop_animation()
        self._hide_progress()
    
    def update_progress(self, step_index: int, message: str = "", 
                       progress_percentage: Optional[float] = None):
        """
        Update progress to a specific step.
        
        Args:
            step_index: Index of current step (0-based)
            message: Optional status message
            progress_percentage: Optional manual progress percentage
        """
        if not self.current_progress:
            return
        
        self.current_progress.current_step = step_index
        
        if message:
            self.current_progress.message = message
        
        # Calculate progress percentage
        if progress_percentage is not None:
            self.current_progress.progress_percentage = progress_percentage
        else:
            # Calculate based on steps
            if self.current_progress.steps:
                completed_weight = sum(
                    step.weight for i, step in enumerate(self.current_progress.steps)
                    if i < step_index
                )
                total_weight = sum(step.weight for step in self.current_progress.steps)
                self.current_progress.progress_percentage = (completed_weight / total_weight) * 100
            else:
                self.current_progress.progress_percentage = (step_index / self.current_progress.total_steps) * 100
        
        # Mark current step as completed
        if (self.current_progress.steps and 
            0 <= step_index < len(self.current_progress.steps)):
            self.current_progress.steps[step_index].completed = True
        
        # Update estimated time remaining
        self._update_time_estimate()
        
        self._update_display()
    
    def complete_step(self, step_index: int, message: str = ""):
        """
        Mark a specific step as completed.
        
        Args:
            step_index: Index of step to complete
            message: Optional completion message
        """
        if (self.current_progress and self.current_progress.steps and
            0 <= step_index < len(self.current_progress.steps)):
            
            self.current_progress.steps[step_index].completed = True
            
            if message:
                self.current_progress.steps[step_index].description = message
        
        self.update_progress(step_index + 1, message)
    
    def set_step_error(self, step_index: int, error_message: str):
        """
        Mark a step as having an error.
        
        Args:
            step_index: Index of step with error
            error_message: Error description
        """
        if (self.current_progress and self.current_progress.steps and
            0 <= step_index < len(self.current_progress.steps)):
            
            self.current_progress.steps[step_index].error = error_message
            self.current_progress.status = ProgressStatus.ERROR
            self.current_progress.message = f"Fehler: {error_message}"
        
        self._update_display()
    
    def complete_operation(self, success_message: str = "Operation erfolgreich abgeschlossen"):
        """
        Complete the current operation.
        
        Args:
            success_message: Message to show on completion
        """
        if not self.current_progress:
            return
        
        self.current_progress.status = ProgressStatus.COMPLETED
        self.current_progress.progress_percentage = 100.0
        self.current_progress.message = success_message
        
        # Mark all steps as completed
        if self.current_progress.steps:
            for step in self.current_progress.steps:
                if not step.error:
                    step.completed = True
        
        self._stop_animation()
        self._update_display()
        
        # Auto-hide after delay
        self.parent.after(3000, self._hide_progress)
    
    def cancel_operation(self, cancel_message: str = "Operation abgebrochen"):
        """
        Cancel the current operation.
        
        Args:
            cancel_message: Message to show on cancellation
        """
        if not self.current_progress:
            return
        
        self.cancel_requested = True
        self.current_progress.status = ProgressStatus.CANCELLED
        self.current_progress.message = cancel_message
        
        self._stop_animation()
        self._update_display()
        
        # Call cancel callback if provided
        if self.cancel_callback:
            try:
                self.cancel_callback()
            except Exception as e:
                self.logger.error(f"Error in cancel callback: {e}")
        
        # Auto-hide after delay
        self.parent.after(2000, self._hide_progress)
    
    def _show_progress(self):
        """Show the progress indicator."""
        if not self.is_visible:
            self.progress_frame.pack(fill=tk.X, padx=10, pady=5)
            self.is_visible = True
    
    def _hide_progress(self):
        """Hide the progress indicator."""
        if self.is_visible:
            self.progress_frame.pack_forget()
            self.is_visible = False
            self.cancel_button.config(state=tk.DISABLED)
            self._stop_animation()
    
    def _update_display(self):
        """Update the progress display with current information."""
        if not self.current_progress:
            return
        
        # Update progress bar
        self.progress_bar['value'] = self.current_progress.progress_percentage
        
        # Update status label
        status_text = f"{self.current_progress.operation_name}"
        if self.current_progress.status == ProgressStatus.ERROR:
            status_text += " (Fehler)"
            self.status_label.config(fg='red')
        elif self.current_progress.status == ProgressStatus.COMPLETED:
            status_text += " (Abgeschlossen)"
            self.status_label.config(fg='green')
        elif self.current_progress.status == ProgressStatus.CANCELLED:
            status_text += " (Abgebrochen)"
            self.status_label.config(fg='orange')
        else:
            self.status_label.config(fg='black')
        
        self.status_label.config(text=status_text)
        
        # Update detail label
        detail_text = self.current_progress.message
        if self.current_progress.total_steps > 0:
            detail_text += f" ({self.current_progress.current_step}/{self.current_progress.total_steps})"
        self.detail_label.config(text=detail_text)
        
        # Update time estimate
        if self.current_progress.estimated_time_remaining:
            time_text = f"Verbleibende Zeit: {self._format_timedelta(self.current_progress.estimated_time_remaining)}"
            self.time_label.config(text=time_text)
        else:
            self.time_label.config(text="")
        
        # Update step list
        if self.show_details and self.step_listbox and self.current_progress.steps:
            self.step_listbox.delete(0, tk.END)
            for i, step in enumerate(self.current_progress.steps):
                status_icon = "✓" if step.completed else "❌" if step.error else "⏳"
                step_text = f"{status_icon} {step.name}"
                if step.error:
                    step_text += f" - {step.error}"
                
                self.step_listbox.insert(tk.END, step_text)
                
                # Color coding
                if step.completed:
                    self.step_listbox.itemconfig(i, {'fg': 'green'})
                elif step.error:
                    self.step_listbox.itemconfig(i, {'fg': 'red'})
                elif i == self.current_progress.current_step:
                    self.step_listbox.itemconfig(i, {'fg': 'blue'})
    
    def _update_time_estimate(self):
        """Update estimated time remaining based on progress."""
        if not self.current_progress or not self.current_progress.start_time:
            return
        
        elapsed = datetime.now() - self.current_progress.start_time
        
        if self.current_progress.progress_percentage > 5:  # Only estimate after some progress
            total_estimated = elapsed / (self.current_progress.progress_percentage / 100)
            remaining = total_estimated - elapsed
            
            if remaining.total_seconds() > 0:
                self.current_progress.estimated_time_remaining = remaining
    
    def _format_timedelta(self, td: timedelta) -> str:
        """Format timedelta for display."""
        total_seconds = int(td.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds} Sekunden"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes} Minuten"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self.cancel_operation()
    
    def _start_animation(self):
        """Start indeterminate progress animation."""
        if not self.animation_running:
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(10)
            self.animation_running = True
    
    def _stop_animation(self):
        """Stop indeterminate progress animation."""
        if self.animation_running:
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
            self.animation_running = False
    
    def is_operation_active(self) -> bool:
        """Check if an operation is currently active."""
        return (self.current_progress is not None and 
                self.current_progress.status == ProgressStatus.IN_PROGRESS)
    
    def get_current_progress(self) -> Optional[ProgressInfo]:
        """Get current progress information."""
        return self.current_progress


class StatusFeedback:
    """
    Simple status feedback widget for showing brief status messages.
    
    Used for quick feedback without full progress indication.
    """
    
    def __init__(self, parent_widget: tk.Widget):
        """Initialize status feedback widget."""
        self.parent = parent_widget
        self.status_var = tk.StringVar()
        self.status_var.set("Bereit")
        
        self.status_label = tk.Label(
            parent_widget,
            textvariable=self.status_var,
            font=('Arial', 9),
            fg='gray',
            anchor='w'
        )
        
        # Auto-clear timer
        self.clear_timer: Optional[str] = None
    
    def show_status(self, message: str, duration: int = 3000, color: str = 'black'):
        """
        Show a status message.
        
        Args:
            message: Message to display
            duration: Duration in milliseconds (0 for permanent)
            color: Text color
        """
        self.status_var.set(message)
        self.status_label.config(fg=color)
        
        # Cancel previous timer
        if self.clear_timer:
            self.parent.after_cancel(self.clear_timer)
        
        # Set auto-clear timer
        if duration > 0:
            self.clear_timer = self.parent.after(duration, self._clear_status)
    
    def show_success(self, message: str, duration: int = 3000):
        """Show success message."""
        self.show_status(f"✓ {message}", duration, 'green')
    
    def show_error(self, message: str, duration: int = 5000):
        """Show error message."""
        self.show_status(f"❌ {message}", duration, 'red')
    
    def show_warning(self, message: str, duration: int = 4000):
        """Show warning message."""
        self.show_status(f"⚠️ {message}", duration, 'orange')
    
    def show_info(self, message: str, duration: int = 3000):
        """Show info message."""
        self.show_status(f"ℹ️ {message}", duration, 'blue')
    
    def _clear_status(self):
        """Clear the status message."""
        self.status_var.set("Bereit")
        self.status_label.config(fg='gray')
        self.clear_timer = None
    
    def pack(self, **kwargs):
        """Pack the status label."""
        self.status_label.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the status label."""
        self.status_label.grid(**kwargs)


class ProgressManager:
    """
    Manager for coordinating multiple progress indicators and status feedback.
    
    Provides a centralized way to manage progress for different operations
    across the application.
    """
    
    def __init__(self):
        """Initialize progress manager."""
        self.indicators: Dict[str, ProgressIndicator] = {}
        self.status_feedbacks: Dict[str, StatusFeedback] = {}
        self.active_operations: Dict[str, ProgressInfo] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_indicator(self, name: str, indicator: ProgressIndicator):
        """Register a progress indicator."""
        self.indicators[name] = indicator
    
    def register_status_feedback(self, name: str, feedback: StatusFeedback):
        """Register a status feedback widget."""
        self.status_feedbacks[name] = feedback
    
    def start_operation(self, indicator_name: str, operation_type: OperationType,
                       operation_name: str, steps: List[ProgressStep],
                       cancel_callback: Optional[Callable] = None) -> str:
        """
        Start an operation with progress indication.

        Returns:
            Operation ID for tracking
        """
        if indicator_name not in self.indicators:
            self.logger.warning(f"Progress indicator '{indicator_name}' not found")
            return ""

        operation_id = f"{indicator_name}::{int(time.time())}"

        indicator = self.indicators[indicator_name]
        indicator.start_operation(operation_type, operation_name, steps, cancel_callback)

        self.active_operations[operation_id] = indicator.get_current_progress()

        return operation_id

    def _extract_indicator_name(self, operation_id: str) -> str:
        """Extrahiert den Indicator-Namen aus der operation_id (Format: name::timestamp)."""
        if '::' in operation_id:
            return operation_id.split('::')[0]
        # Fallback für alte IDs: alle Teile bis zum letzten _ joinen
        parts = operation_id.rsplit('_', 1)
        return parts[0] if len(parts) > 1 else operation_id

    def update_operation(self, operation_id: str, step_index: int,
                        message: str = "", progress_percentage: Optional[float] = None):
        """Update an active operation."""
        indicator_name = self._extract_indicator_name(operation_id)

        if indicator_name in self.indicators:
            self.indicators[indicator_name].update_progress(
                step_index, message, progress_percentage
            )

    def complete_operation(self, operation_id: str, success_message: str = ""):
        """Complete an active operation."""
        indicator_name = self._extract_indicator_name(operation_id)

        if indicator_name in self.indicators:
            self.indicators[indicator_name].complete_operation(success_message)

        if operation_id in self.active_operations:
            del self.active_operations[operation_id]
    
    def show_status(self, feedback_name: str, message: str, 
                   status_type: str = 'info', duration: int = 3000):
        """Show a status message."""
        if feedback_name not in self.status_feedbacks:
            self.logger.warning(f"Status feedback '{feedback_name}' not found")
            return
        
        feedback = self.status_feedbacks[feedback_name]
        
        if status_type == 'success':
            feedback.show_success(message, duration)
        elif status_type == 'error':
            feedback.show_error(message, duration)
        elif status_type == 'warning':
            feedback.show_warning(message, duration)
        else:
            feedback.show_info(message, duration)
    
    def get_active_operations(self) -> Dict[str, ProgressInfo]:
        """Get all active operations."""
        return self.active_operations.copy()


# Global progress manager instance
global_progress_manager = ProgressManager()


# Decorator for automatic progress indication
def with_progress(indicator_name: str, operation_type: OperationType, 
                 operation_name: str, steps: List[str]):
    """
    Decorator to automatically add progress indication to functions.
    
    Args:
        indicator_name: Name of progress indicator to use
        operation_type: Type of operation
        operation_name: Human-readable operation name
        steps: List of step names
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create progress steps
            progress_steps = [
                ProgressStep(name=step, description=step) 
                for step in steps
            ]
            
            # Start operation
            operation_id = global_progress_manager.start_operation(
                indicator_name, operation_type, operation_name, progress_steps
            )
            
            try:
                # Execute function with progress updates
                result = func(*args, progress_callback=lambda step, msg="": 
                            global_progress_manager.update_operation(operation_id, step, msg),
                            **kwargs)
                
                # Complete operation
                global_progress_manager.complete_operation(
                    operation_id, f"{operation_name} erfolgreich abgeschlossen"
                )
                
                return result
                
            except Exception as e:
                # Handle error
                global_progress_manager.show_status(
                    indicator_name, f"Fehler: {str(e)}", 'error'
                )
                raise
        
        return wrapper
    return decorator