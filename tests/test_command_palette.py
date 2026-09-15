"""GUI-Tests für command_palette.py (Befehlspalette)."""

import os
import sys
import tkinter as tk
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from command_palette import CommandPalette
from command_registry import Command, CommandRegistry


class TestCommandPalette(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.calls = []
        self.has_result = False
        self.registry = CommandRegistry()
        self.registry.register(Command(
            "a.alpha", "Alpha Befehl", "Test",
            callback=lambda: self.calls.append("alpha")))
        self.registry.register(Command(
            "b.beta", "Beta Befehl", "Test",
            callback=lambda: self.calls.append("beta"),
            requires_result=True))
        self.palette = CommandPalette(
            self.root, self.registry, has_result=lambda: self.has_result)
        self.root.update_idletasks()

    def tearDown(self):
        try:
            self.palette.destroy()
        except tk.TclError:
            pass
        self.root.destroy()

    def test_shows_all_commands_initially(self):
        self.assertEqual(self.palette.listbox.size(), 2)
        self.assertIn("Alpha Befehl", self.palette.listbox.get(0))

    def test_filter_by_query(self):
        self.palette.query_var.set("alpha")
        self.palette._on_query_changed()
        self.assertEqual(self.palette.listbox.size(), 1)
        self.assertIn("Alpha Befehl", self.palette.listbox.get(0))

    def test_empty_state_text(self):
        self.palette.query_var.set("gibtsnicht")
        self.palette._on_query_changed()
        self.assertEqual(self.palette.listbox.size(), 1)
        self.assertEqual(self.palette.listbox.get(0), "Keine Befehle gefunden")

    def test_return_executes_and_closes(self):
        self.palette.query_var.set("alpha")
        self.palette._on_query_changed()
        self.palette._execute_selected()
        self.assertEqual(self.calls, ["alpha"])
        self.assertFalse(self.palette.winfo_exists())

    def test_requires_result_blocked_without_result(self):
        self.palette.query_var.set("beta")
        self.palette._on_query_changed()
        self.palette._execute_selected()
        self.assertEqual(self.calls, [])
        self.assertTrue(self.palette.winfo_exists())
        self.assertEqual(self.palette.status_var.get(),
                         "Benötigt ein ausgewähltes Ergebnis")

    def test_requires_result_runs_with_result(self):
        self.has_result = True
        self.palette.query_var.set("beta")
        self.palette._on_query_changed()
        self.palette._execute_selected()
        self.assertEqual(self.calls, ["beta"])
        self.assertFalse(self.palette.winfo_exists())

    def test_escape_closes(self):
        self.palette._close()
        self.assertFalse(self.palette.winfo_exists())

    def test_arrow_navigation(self):
        self.palette._move_selection(1)
        self.assertEqual(self.palette.listbox.curselection(), (1,))
        self.palette._move_selection(1)  # clamped at last row
        self.assertEqual(self.palette.listbox.curselection(), (1,))
        self.palette._move_selection(-1)
        self.assertEqual(self.palette.listbox.curselection(), (0,))


if __name__ == "__main__":
    unittest.main()
