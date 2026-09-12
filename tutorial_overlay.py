"""
Tutorial overlay system for KI Analysetool.

Provides a semi-transparent overlay that highlights a target widget and shows
a short explanation with "Next" / "Skip" navigation. Useful for onboarding
and guided learning steps.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, List, Dict, Any


class TutorialOverlay:
    """A reusable tutorial overlay that highlights widgets step by step."""

    def __init__(self, parent: tk.Tk, steps: List[Dict[str, Any]] = None,
                 on_finish: Optional[Callable] = None,
                 on_skip: Optional[Callable] = None):
        self.parent = parent
        self.steps = steps or []
        self.on_finish = on_finish
        self.on_skip = on_skip
        self.current_index = 0
        self._overlay: Optional[tk.Toplevel] = None
        self._highlight: Optional[tk.Toplevel] = None

    def start(self):
        """Start the tutorial from the first step."""
        if not self.steps:
            self._finish()
            return
        self.current_index = 0
        self._show_step()

    def _show_step(self):
        self._destroy_overlays()

        step = self.steps[self.current_index]
        target = step.get("target")
        title = step.get("title", "Tipp")
        text = step.get("text", "")

        if target is None or not self._widget_exists(target):
            # Skip missing widgets and continue.
            self._next()
            return

        self._create_highlight(target)
        self._create_info_box(title, text)

    def _widget_exists(self, widget) -> bool:
        try:
            return widget.winfo_exists()
        except tk.TclError:
            return False

    def _create_highlight(self, target):
        """Create a highlighted frame around the target widget."""
        try:
            x = target.winfo_rootx()
            y = target.winfo_rooty()
            width = target.winfo_width()
            height = target.winfo_height()
        except tk.TclError:
            return

        highlight = tk.Toplevel(self.parent)
        highlight.wm_overrideredirect(True)
        highlight.attributes("-topmost", True)
        highlight.attributes("-transparentcolor", "#fffffe")
        highlight.geometry(f"{width + 8}x{height + 8}+{x - 4}+{y - 4}")

        canvas = tk.Canvas(highlight, bg="#fffffe", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        # Draw a yellow border rectangle
        canvas.create_rectangle(
            2, 2, width + 6, height + 6,
            outline="#ffcc00", width=4, fill=""
        )

        self._highlight = highlight

    def _create_info_box(self, title: str, text: str):
        """Create the info box with navigation buttons."""
        box = tk.Toplevel(self.parent)
        box.wm_overrideredirect(True)
        box.attributes("-topmost", True)
        box.resizable(False, False)

        frame = ttk.Frame(box, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=title, font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(frame, text=text, wraplength=320, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 10))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)

        is_last = self.current_index >= len(self.steps) - 1
        next_label = "Fertig" if is_last else "Weiter"

        def next_action():
            if is_last:
                self._finish()
            else:
                self._next()

        ttk.Button(btn_frame, text=next_label, command=next_action).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Überspringen", command=self._skip).pack(side=tk.RIGHT)

        # Position the box below or beside the highlight, centered on screen if needed.
        box.update_idletasks()
        bw = box.winfo_width()
        bh = box.winfo_height()
        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        px = self.parent.winfo_rootx()
        py = self.parent.winfo_rooty()
        x = px + max(20, (pw - bw) // 2)
        y = py + max(20, (ph - bh) // 2)
        box.geometry(f"+{x}+{y}")

        self._overlay = box

    def _next(self):
        self.current_index += 1
        if self.current_index >= len(self.steps):
            self._finish()
        else:
            self._show_step()

    def _skip(self):
        self._destroy_overlays()
        if self.on_skip:
            self.on_skip()

    def _finish(self):
        self._destroy_overlays()
        if self.on_finish:
            self.on_finish()

    def _destroy_overlays(self):
        if self._overlay is not None:
            try:
                self._overlay.destroy()
            except tk.TclError:
                pass
            self._overlay = None
        if self._highlight is not None:
            try:
                self._highlight.destroy()
            except tk.TclError:
                pass
            self._highlight = None
