import sys
import unittest
from pathlib import Path
from unittest import mock

import app_paths


class TestAppPaths(unittest.TestCase):

    def test_dev_mode_data_dir_is_cwd(self):
        with mock.patch.object(sys, "frozen", False, create=True):
            self.assertEqual(app_paths.get_data_dir(), Path.cwd())

    def test_dev_mode_resource_path_is_repo(self):
        with mock.patch.object(sys, "frozen", False, create=True):
            path = app_paths.resource_path("HELP.md")
            self.assertTrue(path.exists())
            self.assertEqual(path.parent, Path(app_paths.__file__).resolve().parent)

    def test_frozen_macos_data_dir(self):
        with mock.patch.object(sys, "frozen", True, create=True), \
             mock.patch.object(sys, "platform", "darwin"), \
             mock.patch.object(Path, "mkdir"):
            path = app_paths.get_data_dir()
            self.assertIn("Application Support", str(path))
            self.assertEqual(path.name, app_paths.APP_NAME)

    def test_frozen_windows_data_dir(self):
        with mock.patch.object(sys, "frozen", True, create=True), \
             mock.patch.object(sys, "platform", "win32"), \
             mock.patch.dict("os.environ", {"APPDATA": "C:/Users/x/AppData/Roaming"}), \
             mock.patch.object(Path, "mkdir"):
            path = app_paths.get_data_dir()
            self.assertEqual(path.parent, Path("C:/Users/x/AppData/Roaming"))

    def test_frozen_linux_data_dir(self):
        with mock.patch.object(sys, "frozen", True, create=True), \
             mock.patch.object(sys, "platform", "linux"), \
             mock.patch.dict("os.environ",
                             {"XDG_DATA_HOME": "/home/x/.local/share"}), \
             mock.patch.object(Path, "mkdir"):
            path = app_paths.get_data_dir()
            self.assertEqual(path.parent, Path("/home/x/.local/share"))

    def test_frozen_resource_path_uses_meipass(self):
        with mock.patch.object(sys, "frozen", True, create=True), \
             mock.patch.object(sys, "_MEIPASS", "/tmp/_mei123", create=True):
            self.assertEqual(app_paths.resource_path("HELP.md"),
                             Path("/tmp/_mei123/HELP.md"))


class TestSpecFile(unittest.TestCase):

    def test_spec_bundles_docs_and_tkinterdnd(self):
        spec = Path(__file__).resolve().parent.parent / "ki_analysetool.spec"
        content = spec.read_text(encoding="utf-8")
        self.assertIn("HELP.md", content)
        self.assertIn("USER_GUIDE.md", content)
        self.assertIn("tkinterdnd2", content)
        self.assertIn("keyring.backends", content)


if __name__ == "__main__":
    unittest.main()
