"""
Shared GUI utilities for the KI Analysetool application.

This module contains reusable helpers for thread-safe UI updates, common
dialogs, and safe window operations so that GUI code stays readable and
robust.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Callable, Optional, Any


def is_window_alive(window: tk.Tk) -> bool:
    """Return True if the Tkinter window/widget still exists."""
    try:
        return window.winfo_exists()
    except tk.TclError:
        return False


def safe_after(window: tk.Tk, delay_ms: int, callback: Callable, *args: Any):
    """Schedule a callback on the main thread only if the window is alive."""
    if not is_window_alive(window):
        return
    try:
        window.after(delay_ms, callback, *args)
    except tk.TclError:
        pass


def safe_progress_start(progress_indicator, message: str, window: Optional[tk.Tk] = None):
    """Start a progress indicator if the UI is still alive."""
    if window is not None and not is_window_alive(window):
        return
    try:
        progress_indicator.start(message)
    except tk.TclError:
        pass


def safe_progress_stop(progress_indicator, window: Optional[tk.Tk] = None):
    """Stop a progress indicator if the UI is still alive."""
    if window is not None and not is_window_alive(window):
        return
    try:
        progress_indicator.stop()
    except tk.TclError:
        pass


def show_info(parent, title: str, message: str):
    """Thread-safe info dialog."""
    if is_window_alive(parent):
        try:
            messagebox.showinfo(title, message, parent=parent)
        except tk.TclError:
            pass


def show_error(parent, title: str, message: str):
    """Thread-safe error dialog."""
    if is_window_alive(parent):
        try:
            messagebox.showerror(title, message, parent=parent)
        except tk.TclError:
            pass


def ask_string(parent, title: str, prompt: str, initialvalue: str = "") -> Optional[str]:
    """Simple input dialog with validation."""
    if not is_window_alive(parent):
        return None
    try:
        return simpledialog.askstring(title, prompt, parent=parent, initialvalue=initialvalue)
    except tk.TclError:
        return None


def create_labeled_entry(parent, label_text: str, variable, help_text: Optional[str] = None,
                         show: Optional[str] = None):
    """Create a labeled entry row with an optional help indicator."""
    from help_tooltip import add_help_indicator

    frame = ttk.Frame(parent)
    frame.pack(fill=tk.X, pady=(0, 5))
    ttk.Label(frame, text=label_text).pack(side=tk.LEFT)
    if help_text:
        add_help_indicator(frame, help_text)
    entry = ttk.Entry(frame, textvariable=variable, show=show)
    entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
    return entry
