"""Unit tests for learning_path.py."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from learning_path import LearningPath, DEFAULT_LEARNING_STEPS
from user_profile import UserProfileManager


class TestLearningPath(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        UserProfileManager._instance = None
        profile_manager = UserProfileManager(config_dir=self.tmpdir.name)
        self.learning_path = LearningPath(steps=DEFAULT_LEARNING_STEPS, profile_manager=profile_manager)

    def test_initial_progress(self):
        progress = self.learning_path.progress()
        self.assertEqual(progress["completed"], 0)
        self.assertEqual(progress["total"], len(DEFAULT_LEARNING_STEPS))
        self.assertEqual(progress["percent"], 0)
        self.assertFalse(progress["all_done"])

    def test_complete_steps(self):
        first = self.learning_path.current_step()
        self.assertIsNotNone(first)
        self.learning_path.complete(first.id)
        self.assertTrue(self.learning_path.is_completed(first.id))

        progress = self.learning_path.progress()
        self.assertEqual(progress["completed"], 1)
        self.assertGreater(progress["percent"], 0)

    def test_all_done(self):
        for step in self.learning_path.steps:
            self.learning_path.complete(step.id)
        progress = self.learning_path.progress()
        self.assertTrue(progress["all_done"])
        self.assertIsNone(self.learning_path.current_step())

    def test_persistence(self):
        self.learning_path.complete("first_analysis")
        UserProfileManager._instance = None
        profile_manager = UserProfileManager(config_dir=self.tmpdir.name)
        path2 = LearningPath(steps=DEFAULT_LEARNING_STEPS, profile_manager=profile_manager)
        self.assertTrue(path2.is_completed("first_analysis"))

    def test_invalid_step_raises(self):
        with self.assertRaises(ValueError):
            self.learning_path.complete("does_not_exist")

    def test_ui_items_format(self):
        items = self.learning_path.to_ui_items()
        self.assertEqual(len(items), len(DEFAULT_LEARNING_STEPS))
        first = items[0]
        self.assertIn("id", first)
        self.assertIn("title", first)
        self.assertIn("description", first)
        self.assertIn("completed", first)


if __name__ == "__main__":
    unittest.main()
