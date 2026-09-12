"""Unit tests for prompt_library.py."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_library import PromptLibrary, DEFAULT_PROMPTS


class TestPromptLibrary(unittest.TestCase):

    def setUp(self):
        self.library = PromptLibrary()

    def test_all_prompts_have_placeholder(self):
        for template in self.library.all():
            self.assertIn("{text}", template.prompt,
                          f"Template '{template.title}' fehlt {{text}}-Platzhalter")

    def test_by_id(self):
        template = self.library.by_id("summary_short")
        self.assertEqual(template.title, "Kurze Zusammenfassung")
        self.assertIn("{text}", template.prompt)

    def test_by_id_missing_raises(self):
        with self.assertRaises(KeyError):
            self.library.by_id("does_not_exist")

    def test_format(self):
        template = self.library.by_id("summary_short")
        prompt = template.format(content="Beispieltext")
        self.assertIn("Beispieltext", prompt)
        self.assertNotIn("{text}", prompt)

    def test_by_category(self):
        categories = self.library.by_category()
        self.assertGreater(len(categories), 0)
        for category, templates in categories.items():
            self.assertGreater(len(templates), 0)

    def test_for_difficulty(self):
        beginner = self.library.for_difficulty("beginner")
        self.assertTrue(all(t.difficulty == "beginner" for t in beginner))

        intermediate = self.library.for_difficulty("intermediate")
        levels = {t.difficulty for t in intermediate}
        self.assertIn("beginner", levels)
        self.assertIn("intermediate", levels)

        expert = self.library.for_difficulty("expert")
        self.assertEqual(len(expert), len(DEFAULT_PROMPTS))

    def test_menu_dict_format(self):
        menu = self.library.to_menu_dict()
        self.assertGreater(len(menu), 0)
        for category, items in menu.items():
            self.assertGreater(len(items), 0)
            self.assertIn("id", items[0])
            self.assertIn("title", items[0])
            self.assertIn("description", items[0])


if __name__ == "__main__":
    unittest.main()
