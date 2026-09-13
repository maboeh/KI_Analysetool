import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

from help_tooltip import add_help_indicator, show_context_help


class TestHelpTooltip(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.frame = ttk.Frame(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_indicator_is_keyboard_focusable_button(self):
        indicator = add_help_indicator(self.frame, "Hilfetext")
        self.assertIsInstance(indicator, ttk.Button)
        self.assertEqual(str(indicator.cget("takefocus")), "1")

    def test_context_help_closes_with_escape(self):
        window = show_context_help(self.frame, "Hilfetext")
        self.assertTrue(window.winfo_exists())
        self.assertTrue(window.bind("<Escape>"))
        window.destroy()

    def test_indicator_opens_context_help(self):
        indicator = add_help_indicator(self.frame, "Hilfetext")
        with patch("help_tooltip.show_context_help") as show_help:
            indicator.invoke()
        show_help.assert_called_once_with(self.frame, "Hilfetext")


if __name__ == "__main__":
    unittest.main()
