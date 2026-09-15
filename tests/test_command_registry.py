"""Tests für command_registry.py (Befehlsregister, Suche, Shortcut-Mapping)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from command_registry import (
    Command,
    CommandRegistry,
    accelerator_label,
    tk_binding,
)


def _command(command_id, label="Befehl", category="Test", **kwargs):
    return Command(id=command_id, label=label, category=category,
                   callback=lambda: None, **kwargs)


class TestCommandRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = CommandRegistry()

    def test_register_and_get(self):
        command = _command("a.test", "Alpha")
        self.registry.register(command)
        self.assertIs(self.registry.get("a.test"), command)
        self.assertIsNone(self.registry.get("fehlt"))

    def test_duplicate_id_raises(self):
        self.registry.register(_command("a.test"))
        with self.assertRaises(ValueError):
            self.registry.register(_command("a.test", label="Anderes"))

    def test_all_preserves_registration_order(self):
        for command_id in ("c.dritte", "a.erste", "b.zweite"):
            self.registry.register(_command(command_id))
        self.assertEqual(
            [c.id for c in self.registry.all()],
            ["c.dritte", "a.erste", "b.zweite"],
        )

    def test_by_category_groups_in_order(self):
        self.registry.register(_command("a", category="Export"))
        self.registry.register(_command("b", category="Ergebnisse"))
        self.registry.register(_command("c", category="Export"))
        grouped = self.registry.by_category()
        self.assertEqual(list(grouped.keys()), ["Export", "Ergebnisse"])
        self.assertEqual([c.id for c in grouped["Export"]], ["a", "c"])

    def test_search_empty_returns_all(self):
        for index in range(20):
            self.registry.register(_command(f"c{index}"))
        self.assertEqual(len(self.registry.search("")), 12)
        self.assertEqual(len(self.registry.search("", limit=25)), 20)
        self.assertEqual(len(self.registry.search("   ")), 12)

    def test_search_substring_beats_subsequence(self):
        self.registry.register(_command("sub", "Quellenbelege prüfen"))
        self.registry.register(_command("seq", "Beispiel-Export"))
        results = self.registry.search("bel")
        ids = [c.id for c in results]
        self.assertIn("sub", ids)
        self.assertIn("seq", ids)
        self.assertEqual(ids[0], "sub")  # Substring-Treffer vor Subsequenz

    def test_search_prefix_bonus(self):
        self.registry.register(_command("mid", "Extrahierte Daten bearbeiten"))
        self.registry.register(_command("pre", "Daten exportieren"))
        results = self.registry.search("daten")
        self.assertEqual(results[0].id, "pre")

    def test_search_keywords_and_category(self):
        self.registry.register(_command("a", "Batch-Export", category="Export",
                                        keywords=("zip", "archiv")))
        self.registry.register(_command("b", "Einstellungen",
                                        category="Einstellungen"))
        self.assertEqual([c.id for c in self.registry.search("zip")], ["a"])
        self.assertIn("b", [c.id for c in self.registry.search("einstellung")])

    def test_search_casefold_umlauts(self):
        self.registry.register(_command("a", "Änderungen prüfen"))
        self.assertEqual(len(self.registry.search("änderung")), 1)
        self.assertEqual(len(self.registry.search("ÄNDERUNG")), 1)

    def test_search_no_match(self):
        self.registry.register(_command("a", "Backup erstellen"))
        self.assertEqual(self.registry.search("xyzq"), [])


class TestTkBinding(unittest.TestCase):
    def test_darwin_adds_command_variant(self):
        self.assertEqual(
            tk_binding("Ctrl+K", platform="darwin"),
            ["<Command-k>", "<Control-k>"],
        )

    def test_linux_only_control(self):
        self.assertEqual(tk_binding("Ctrl+K", platform="linux"),
                         ["<Control-k>"])

    def test_shift_uses_uppercase_letter(self):
        self.assertEqual(tk_binding("Ctrl+Shift+E", platform="win32"),
                         ["<Control-Shift-E>"])
        self.assertEqual(tk_binding("Ctrl+Shift+E", platform="darwin"),
                         ["<Command-Shift-E>", "<Control-Shift-E>"])

    def test_named_key_unchanged(self):
        self.assertEqual(tk_binding("Ctrl+Return", platform="linux"),
                         ["<Control-Return>"])

    def test_comma_maps_to_keysym(self):
        self.assertEqual(tk_binding("Ctrl+,", platform="linux"),
                         ["<Control-comma>"])
        self.assertEqual(tk_binding("Ctrl+,", platform="darwin"),
                         ["<Command-comma>", "<Control-comma>"])

    def test_invalid_shortcut_raises(self):
        with self.assertRaises(ValueError):
            tk_binding("Ctrl", platform="linux")


class TestAcceleratorLabel(unittest.TestCase):
    def test_darwin_symbols(self):
        self.assertEqual(accelerator_label("Ctrl+K", platform="darwin"), "⌘K")
        self.assertEqual(accelerator_label("Ctrl+Shift+E", platform="darwin"),
                         "⇧⌘E")
        self.assertEqual(accelerator_label("Ctrl+Return", platform="darwin"),
                         "⌘↩")

    def test_other_platforms_text(self):
        self.assertEqual(accelerator_label("Ctrl+K", platform="win32"),
                         "Ctrl+K")
        self.assertEqual(accelerator_label("Ctrl+Shift+E", platform="linux"),
                         "Ctrl+Shift+E")
        self.assertEqual(accelerator_label("Ctrl+Return", platform="win32"),
                         "Ctrl+Enter")


if __name__ == "__main__":
    unittest.main()
