"""Befehlspalette (Quick-Launcher) für das KI Analysetool.

Zeigt alle im :class:`CommandRegistry` registrierten Befehle filterbar an
und führt den ausgewählten Befehl per Enter oder Doppelklick aus. Befehle
mit ``requires_result`` werden ohne aktuelles Ergebnis ausgegraut und bei
Ausführung mit einem Hinweis abgelehnt statt ausgeführt.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, List

from command_registry import Command, CommandRegistry, accelerator_label


class CommandPalette(tk.Toplevel):
    """Modales Schnellwahlfenster für alle registrierten Befehle."""

    WIDTH = 560
    MAX_ROWS = 12

    def __init__(self, parent, registry: CommandRegistry,
                 has_result: Callable[[], bool]):
        super().__init__(parent)
        self.registry = registry
        self.has_result = has_result
        self._matches: List[Command] = []
        self._last_query = ""

        self.title("Befehlspalette")
        self.transient(parent)
        self.resizable(False, False)

        self.query_var = tk.StringVar()
        self.status_var = tk.StringVar()

        self.entry = ttk.Entry(self, textvariable=self.query_var)
        self.entry.pack(fill=tk.X, padx=8, pady=(8, 4))
        self.entry.bind("<KeyRelease>", self._on_query_changed)
        self.entry.bind("<Down>", lambda _event: self._move_selection(1))
        self.entry.bind("<Up>", lambda _event: self._move_selection(-1))
        self.entry.bind("<Return>", lambda _event: self._execute_selected())
        self.entry.bind("<Escape>", lambda _event: self._close())

        self.listbox = tk.Listbox(
            self, height=self.MAX_ROWS, activestyle="dotbox",
            font=("Segoe UI", 10), exportselection=False,
        )
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 4))
        self.listbox.bind("<Return>", lambda _event: self._execute_selected())
        self.listbox.bind("<Escape>", lambda _event: self._close())
        self.listbox.bind("<Double-Button-1>",
                          lambda _event: self._execute_selected())
        self.bind("<Escape>", lambda _event: self._close())

        self.status_label = ttk.Label(self, textvariable=self.status_var,
                                      foreground="#666666")
        self.status_label.pack(fill=tk.X, padx=8, pady=(0, 8))

        # Zentriert über dem Elternfenster positionieren
        self.update_idletasks()
        try:
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
        except tk.TclError:
            parent_x = parent_y = 0
            parent_width = parent_height = 800
        height = 34 + self.MAX_ROWS * 22 + 30
        x = parent_x + max((parent_width - self.WIDTH) // 2, 0)
        y = parent_y + max(parent_height // 5, 30)
        self.geometry(f"{self.WIDTH}x{height}+{x}+{y}")

        self._refresh()
        self.entry.focus_set()
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def _refresh(self):
        """Baut die Trefferliste anhand des aktuellen Query neu auf."""
        self.status_var.set("")
        self._matches = self.registry.search(self.query_var.get(),
                                             self.MAX_ROWS)
        self.listbox.delete(0, tk.END)
        if not self._matches:
            self.listbox.insert(tk.END, "Keine Befehle gefunden")
            self.listbox.itemconfig(0, fg="#888888")
            return
        result_available = self.has_result()
        for index, command in enumerate(self._matches):
            text = f"{command.label.ljust(40)}·  {command.category}"
            if command.shortcut:
                text += f"   {accelerator_label(command.shortcut)}"
            self.listbox.insert(tk.END, text)
            if command.requires_result and not result_available:
                self.listbox.itemconfig(index, fg="#888888")
        self.listbox.selection_set(0)
        self.listbox.activate(0)

    def _on_query_changed(self, _event=None):
        query = self.query_var.get()
        if query != self._last_query:
            self._last_query = query
            self._refresh()

    def _move_selection(self, delta: int):
        if not self._matches:
            return "break"
        selection = self.listbox.curselection()
        index = selection[0] if selection else 0
        index = max(0, min(index + delta, len(self._matches) - 1))
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self.listbox.see(index)
        return "break"

    def _execute_selected(self):
        if not self._matches:
            return "break"
        selection = self.listbox.curselection()
        index = selection[0] if selection else 0
        command = self._matches[index]
        if command.requires_result and not self.has_result():
            self.status_var.set("Benötigt ein ausgewähltes Ergebnis")
            return "break"
        self._close()
        command.callback()
        return "break"

    def _close(self):
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()
        return "break"
