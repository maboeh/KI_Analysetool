"""
Inline help and documentation support for KI Analysetool.

Provides small "?" indicators that show a delayed tooltip on hover and
a non-modal help window that displays the user guide.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from pathlib import Path


def add_help_indicator(parent, help_text, delay=500):
    """
    Add a small '?' label next to the parent widget that shows a tooltip
    after the user hovers for `delay` milliseconds.
    """
    indicator = ttk.Label(parent, text="?", foreground="blue", cursor="question_arrow")
    indicator.pack(side=tk.LEFT, padx=(2, 0))
    
    tooltip = None
    hover_after = None
    
    def show_tooltip(event=None):
        nonlocal tooltip
        if tooltip is not None:
            return
        
        x = event.x_root + 15 if event else parent.winfo_rootx() + 20
        y = event.y_root + 15 if event else parent.winfo_rooty() + 20
        
        tooltip = tk.Toplevel(parent)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        tooltip.attributes("-topmost", True)
        
        label = ttk.Label(
            tooltip,
            text=help_text,
            background="#ffffe0",
            foreground="#000000",
            relief=tk.SOLID,
            borderwidth=1,
            wraplength=300,
            padding=(5, 3)
        )
        label.pack()
    
    def schedule_tooltip(event):
        nonlocal hover_after
        hover_after = parent.after(delay, lambda: show_tooltip(event))
    
    def hide_tooltip(event=None):
        nonlocal tooltip, hover_after
        if hover_after is not None:
            parent.after_cancel(hover_after)
            hover_after = None
        if tooltip is not None:
            tooltip.destroy()
            tooltip = None
    
    indicator.bind("<Enter>", schedule_tooltip)
    indicator.bind("<Leave>", hide_tooltip)
    
    return indicator


def show_help_window(parent, title="KI Analysetool - Hilfe & Dokumentation"):
    """Open a non-modal help window showing the user guide."""
    help_path = Path(__file__).parent / "USER_GUIDE.md"
    
    window = tk.Toplevel(parent)
    window.title(title)
    window.geometry("800x700")
    window.transient(parent)
    
    main_frame = ttk.Frame(window, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(main_frame, text=title, font=("Segoe UI", 14, "bold")).pack(anchor=tk.W, pady=(0, 10))
    
    text_widget = scrolledtext.ScrolledText(
        main_frame,
        wrap=tk.WORD,
        state=tk.DISABLED,
        font=("Segoe UI", 10),
        padx=10,
        pady=10
    )
    text_widget.pack(fill=tk.BOTH, expand=True)
    
    if help_path.exists():
        content = help_path.read_text(encoding="utf-8")
    else:
        content = "Die Dokumentation (USER_GUIDE.md) wurde nicht gefunden."
    
    text_widget.config(state=tk.NORMAL)
    text_widget.insert(tk.END, content)
    text_widget.config(state=tk.DISABLED)
    
    ttk.Button(main_frame, text="Schließen", command=window.destroy).pack(pady=(10, 0))
    
    return window
