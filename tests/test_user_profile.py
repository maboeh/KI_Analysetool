"""Unit tests for user_profile.py."""

import json
import os
import tempfile
import unittest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from user_profile import UserProfile, UserProfileManager


class TestUserProfile(unittest.TestCase):

    def test_defaults(self):
        profile = UserProfile()
        self.assertEqual(profile.experience_level, "beginner")
        self.assertFalse(profile.onboarding_completed)
        self.assertFalse(profile.onboarding_skipped)
        self.assertTrue(profile.show_learning_panel)
        self.assertEqual(profile.completed_tutorial_steps, [])

    def test_mark_onboarding_complete(self):
        profile = UserProfile()
        profile.mark_onboarding_complete()
        self.assertTrue(profile.onboarding_completed)

    def test_complete_step(self):
        profile = UserProfile()
        profile.complete_step("first_analysis")
        self.assertIn("first_analysis", profile.completed_tutorial_steps)
        profile.complete_step("first_analysis")
        self.assertEqual(len(profile.completed_tutorial_steps), 1)

    def test_dismiss_help(self):
        profile = UserProfile()
        profile.dismiss_help("prompt_help")
        self.assertTrue(profile.is_help_dismissed("prompt_help"))

    def test_to_dict_roundtrip(self):
        profile = UserProfile(experience_level="expert", onboarding_completed=True)
        profile.complete_step("step1")
        data = profile.to_dict()
        restored = UserProfile.from_dict(data)
        self.assertEqual(restored.experience_level, "expert")
        self.assertTrue(restored.onboarding_completed)
        self.assertIn("step1", restored.completed_tutorial_steps)


class TestUserProfileManager(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        # Reset singleton state for each test
        UserProfileManager._instance = None
        self.manager = UserProfileManager(config_dir=self.tmpdir.name)

    def test_skip_onboarding_is_distinct_from_completion(self):
        self.manager.skip_onboarding()
        self.assertTrue(self.manager.profile.onboarding_skipped)
        self.assertFalse(self.manager.profile.onboarding_completed)

    def test_learning_panel_preference_persists(self):
        self.manager.set_learning_panel_visibility(False)
        UserProfileManager._instance = None
        fresh = UserProfileManager(config_dir=self.tmpdir.name)
        self.assertFalse(fresh.profile.show_learning_panel)

    def test_singleton(self):
        other = UserProfileManager(config_dir=self.tmpdir.name)
        self.assertIs(self.manager, other)

    def test_persistence(self):
        self.manager.set_experience_level("intermediate")
        self.manager.complete_onboarding()
        self.manager.complete_step("first_analysis")

        # Simulate fresh instance reading from disk
        UserProfileManager._instance = None
        fresh = UserProfileManager(config_dir=self.tmpdir.name)
        self.assertEqual(fresh.profile.experience_level, "intermediate")
        self.assertTrue(fresh.profile.onboarding_completed)
        self.assertIn("first_analysis", fresh.profile.completed_tutorial_steps)

    def test_invalid_level_raises(self):
        with self.assertRaises(ValueError):
            self.manager.set_experience_level("guru")


if __name__ == "__main__":
    unittest.main()
