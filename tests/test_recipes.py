import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from projects import ProjectManager
from recipes import RecipeManager
from results_manager import ResultsManager


class TestRecipeManager(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.db_path = str(self.tmp / "results.db")
        ResultsManager(self.db_path, str(self.tmp / "results"))  # Schema anlegen
        self.manager = RecipeManager(self.db_path)
        self.projects = ProjectManager(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_create_and_get(self):
        recipe = self.manager.create_recipe(
            name="Wochenzusammenfassung",
            prompt_template="Fasse zusammen: {text}",
            source_type="website",
            model="gpt-4o-mini",
            follow_up_actions=["translate"],
            export_format="pdf",
        )
        loaded = self.manager.get_recipe(recipe.id)
        self.assertEqual(loaded.name, "Wochenzusammenfassung")
        self.assertEqual(loaded.prompt_template, "Fasse zusammen: {text}")
        self.assertEqual(loaded.source_type, "website")
        self.assertEqual(loaded.model, "gpt-4o-mini")
        self.assertEqual(loaded.follow_up_actions, ["translate"])
        self.assertEqual(loaded.export_format, "pdf")

    def test_validation(self):
        with self.assertRaises(ValueError):
            self.manager.create_recipe("", "prompt")
        with self.assertRaises(ValueError):
            self.manager.create_recipe("Name", "  ")

    def test_list_and_project_filter(self):
        project = self.projects.create_project("P1")
        own = self.manager.create_recipe("Projektrezept", "p", project_id=project.id)
        global_recipe = self.manager.create_recipe("Global", "p")

        all_recipes = self.manager.list_recipes()
        self.assertEqual(len(all_recipes), 2)

        project_recipes = self.manager.list_recipes(project_id=project.id)
        self.assertEqual({r.id for r in project_recipes}, {own.id, global_recipe.id})

    def test_update(self):
        recipe = self.manager.create_recipe("Alt", "p")
        self.assertTrue(self.manager.update_recipe(
            recipe.id, name="Neu", follow_up_actions=["summarize"]))
        loaded = self.manager.get_recipe(recipe.id)
        self.assertEqual(loaded.name, "Neu")
        self.assertEqual(loaded.follow_up_actions, ["summarize"])
        self.assertFalse(self.manager.update_recipe(recipe.id, unknown_field=1))

    def test_delete(self):
        recipe = self.manager.create_recipe("Weg", "p")
        self.assertTrue(self.manager.delete_recipe(recipe.id))
        self.assertIsNone(self.manager.get_recipe(recipe.id))

    def test_project_delete_detaches_recipe(self):
        project = self.projects.create_project("P")
        recipe = self.manager.create_recipe("R", "p", project_id=project.id)
        self.projects.delete_project(project.id)
        loaded = self.manager.get_recipe(recipe.id)
        self.assertIsNotNone(loaded)
        self.assertIsNone(loaded.project_id)


if __name__ == "__main__":
    unittest.main()
