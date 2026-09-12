"""
Inline help and documentation support for KI Analysetool.

Provides small "?" indicators that show a delayed tooltip on hover and
a non-modal help window that displays the user guide.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from pathlib import Path
from typing import Optional


class HelpTooltipManager:
    """
    Singleton-style tooltip manager per parent widget.

    Avoids duplicate tooltips, handles delayed show/hide, and makes sure
    the tooltip is destroyed when the parent widget is gone.
    """

    _active_tooltip: Optional[tk.Toplevel] = None
    _active_after_id: Optional[str] = None
    _active_parent: Optional[tk.Widget] = None

    @classmethod
    def _cancel_pending(cls):
        if cls._active_after_id is not None:
            try:
                parent = cls._active_parent
                if parent and parent.winfo_exists():
                    parent.after_cancel(cls._active_after_id)
            except tk.TclError:
                pass
            cls._active_after_id = None
            cls._active_parent = None

    @classmethod
    def _destroy_active(cls):
        cls._cancel_pending()
        if cls._active_tooltip is not None:
            try:
                if cls._active_tooltip.winfo_exists():
                    cls._active_tooltip.destroy()
            except tk.TclError:
                pass
            cls._active_tooltip = None

    @classmethod
    def schedule(cls, parent: tk.Widget, help_text: str, delay: int = 500, event: tk.Event = None):
        """Schedule a tooltip to appear after `delay` milliseconds."""
        cls._destroy_active()

        def show():
            cls._active_after_id = None
            cls._active_parent = None
            if not parent.winfo_exists():
                return
            x = (event.x_root + 15) if event else (parent.winfo_rootx() + 20)
            y = (event.y_root + 15) if event else (parent.winfo_rooty() + 20)

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
                wraplength=350,
                padding=(5, 3),
                justify=tk.LEFT
            )
            label.pack()

            cls._active_tooltip = tooltip

        after_id = parent.after(delay, show)
        cls._active_after_id = after_id
        cls._active_parent = parent

    @classmethod
    def hide(cls):
        """Hide the currently scheduled/active tooltip."""
        cls._destroy_active()


def add_help_indicator(parent, help_text, delay=500):
    """
    Add a small '?' label next to the parent widget that shows a tooltip
    after the user hovers for `delay` milliseconds.
    """
    indicator = ttk.Label(parent, text="?", foreground="blue", cursor="question_arrow")
    indicator.pack(side=tk.LEFT, padx=(2, 0))

    indicator.bind("<Enter>", lambda e: HelpTooltipManager.schedule(parent, help_text, delay, e))
    indicator.bind("<Leave>", lambda e: HelpTooltipManager.hide())

    return indicator


def show_help_window(parent, title="KI Analysetool - Hilfe & Dokumentation",
                     help_file: Optional[Path] = None, anchor: Optional[str] = None):
    """Open a non-modal help window showing the user guide."""
    if help_file is None:
        help_path = Path(__file__).parent / "HELP.md"
        if not help_path.exists():
            help_path = Path(__file__).parent / "USER_GUIDE.md"
    else:
        help_path = Path(help_file)

    window = tk.Toplevel(parent)
    window.title(title)
    window.geometry("850x720")
    window.transient(parent)

    main_frame = ttk.Frame(window, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(1, weight=1)

    ttk.Label(main_frame, text=title, font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

    # Toolbar with search and anchor navigation
    toolbar = ttk.Frame(main_frame)
    toolbar.grid(row=0, column=1, sticky=tk.E, pady=(0, 10))

    text_widget = scrolledtext.ScrolledText(
        main_frame,
        wrap=tk.WORD,
        state=tk.DISABLED,
        font=("Segoe UI", 10),
        padx=10,
        pady=10
    )
    text_widget.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW)

    if help_path.exists():
        content = help_path.read_text(encoding="utf-8")
    else:
        content = "Die Dokumentation wurde nicht gefunden.\nBitte legen Sie HELP.md oder USER_GUIDE.md an."

    text_widget.config(state=tk.NORMAL)
    text_widget.insert(tk.END, content)
    text_widget.config(state=tk.DISABLED)

    def find_text():
        query = search_var.get().strip()
        if not query:
            return
        text_widget.config(state=tk.NORMAL)
        text_widget.tag_remove("found", "1.0", tk.END)
        start = "1.0"
        while True:
            pos = text_widget.search(query, start, stopindex=tk.END, nocase=1)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            text_widget.tag_add("found", pos, end)
            start = end
        text_widget.tag_config("found", background="yellow", foreground="black")
        text_widget.config(state=tk.DISABLED)

    search_var = tk.StringVar()
    search_entry = ttk.Entry(toolbar, textvariable=search_var, width=20)
    search_entry.pack(side=tk.LEFT, padx=(0, 5))
    search_entry.bind("<Return>", lambda e: find_text())
    ttk.Button(toolbar, text="Suchen", command=find_text).pack(side=tk.LEFT, padx=(0, 10))

    def goto_top():
        text_widget.see("1.0")

    ttk.Button(toolbar, text="Nach oben", command=goto_top).pack(side=tk.LEFT)

    ttk.Button(main_frame, text="Schließen", command=window.destroy).grid(row=2, column=1, sticky=tk.E, pady=(10, 0))

    # Optional: jump to a section containing the anchor text
    if anchor:
        text_widget.config(state=tk.NORMAL)
        pos = text_widget.search(anchor, "1.0", stopindex=tk.END, nocase=1)
        if pos:
            text_widget.see(pos)
        text_widget.config(state=tk.DISABLED)

    return window
