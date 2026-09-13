import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backup_manager import (
    BACKUP_MANIFEST_NAME,
    BackupManager,
    BackupValidationError,
    _is_safe_member,
)


class BackupManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.db_path = self.tmp / "results.db"
        self.results_dir = self.tmp / "results"
        self.backup_dir = self.tmp / "backups"
        self.results_dir.mkdir()

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("CREATE TABLE results (id TEXT PRIMARY KEY, title TEXT)")
        conn.execute("INSERT INTO results VALUES ('r1', 'Test')")
        conn.commit()
        conn.close()
        (self.results_dir / "r1.json").write_text('{"id": "r1"}', encoding="utf-8")

        self.manager = BackupManager(
            db_path=str(self.db_path),
            results_dir=str(self.results_dir),
            backup_dir=str(self.backup_dir),
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_zip(self, members: dict) -> Path:
        path = self.tmp / "crafted.zip"
        with zipfile.ZipFile(path, "w") as zf:
            for name, payload in members.items():
                zf.writestr(name, payload)
        return path


class TestBackupCreation(BackupManagerTestCase):
    def test_backup_contains_manifest_and_files(self):
        backup_path = self.manager.create_backup()
        with zipfile.ZipFile(backup_path) as zf:
            names = zf.namelist()
            self.assertIn(BACKUP_MANIFEST_NAME, names)
            self.assertIn("results.db", names)
            self.assertIn("results/r1.json", names)
            manifest = json.loads(zf.read(BACKUP_MANIFEST_NAME).decode("utf-8"))
            self.assertEqual(manifest["format_version"], 1)
            self.assertIn("results.db", manifest["files"])

    def test_config_included_without_api_key(self):
        config = self.tmp / "config.ini"
        config.write_text("[API]\nopenai_key = sk-secret12345678901234567890\n",
                          encoding="utf-8")
        backup_path = self.manager.create_backup(
            include_config=True, config_path=str(config))
        with zipfile.ZipFile(backup_path) as zf:
            self.assertIn("config.ini", zf.namelist())
            content = zf.read("config.ini").decode("utf-8")
            self.assertNotIn("sk-secret", content)


class TestMemberSafety(unittest.TestCase):
    def test_safe_members(self):
        for name in ("results.db", "results/r1.json", "results/sub/x.json",
                     "config.ini", "manifest.json"):
            self.assertTrue(_is_safe_member(name), name)

    def test_unsafe_members(self):
        for name in ("../evil.txt", "results/../../evil", "/etc/passwd",
                     "C:\\Windows\\system32\\evil.dll", "evil.exe",
                     "results/../../../tmp/x", "foo\x00bar"):
            self.assertFalse(_is_safe_member(name), name)


class TestValidation(BackupManagerTestCase):
    def test_valid_backup_passes(self):
        backup_path = self.manager.create_backup()
        report = self.manager.validate_backup(backup_path)
        self.assertTrue(report["valid"], report["errors"])
        self.assertIsNotNone(report["manifest"])

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.manager.validate_backup(str(self.tmp / "nope.zip"))

    def test_non_zip_rejected(self):
        fake = self.tmp / "fake.zip"
        fake.write_text("not a zip")
        report = self.manager.validate_backup(str(fake))
        self.assertFalse(report["valid"])

    def test_zip_slip_rejected(self):
        evil_zip = self._make_zip({"../evil.txt": "böse"})
        report = self.manager.validate_backup(str(evil_zip))
        self.assertFalse(report["valid"])
        self.assertTrue(any("evil.txt" in e for e in report["errors"]))
        with self.assertRaises(BackupValidationError):
            self.manager.restore_backup(str(evil_zip))

    def test_unexpected_top_level_rejected(self):
        evil_zip = self._make_zip({"evil.exe": "MZ"})
        report = self.manager.validate_backup(str(evil_zip))
        self.assertFalse(report["valid"])

    def test_non_sqlite_db_rejected(self):
        bad = self._make_zip({
            "results.db": "definitely not sqlite",
            BACKUP_MANIFEST_NAME: json.dumps({"format_version": 1}),
        })
        report = self.manager.validate_backup(str(bad))
        self.assertFalse(report["valid"])
        self.assertTrue(any("SQLite" in e for e in report["errors"]))

    def test_future_format_version_rejected(self):
        with open(self.db_path, "rb") as db_file:
            db_bytes = db_file.read()
        future = self._make_zip({
            "results.db": db_bytes,
            BACKUP_MANIFEST_NAME: json.dumps({"format_version": 99}),
        })
        report = self.manager.validate_backup(str(future))
        self.assertFalse(report["valid"])


class TestRestore(BackupManagerTestCase):
    def test_restore_creates_safety_backup(self):
        backup_path = self.manager.create_backup()
        # Simuliere Änderung am aktuellen Stand
        (self.results_dir / "r2.json").write_text('{"id": "r2"}', encoding="utf-8")
        before = len(list(self.backup_dir.glob("*.zip")))
        result = self.manager.restore_backup(backup_path)
        after = len(list(self.backup_dir.glob("*.zip")))
        self.assertEqual(after, before + 1)
        self.assertIsNotNone(result["safety_backup"])
        # r2 ist nicht im wiederhergestellten Stand
        self.assertFalse((self.results_dir / "r2.json").exists())

    def test_restore_replaces_database(self):
        backup_path = self.manager.create_backup()
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("DELETE FROM results")
        conn.commit()
        conn.close()
        self.manager.restore_backup(backup_path)
        conn = sqlite3.connect(str(self.db_path))
        rows = conn.execute("SELECT id FROM results").fetchall()
        conn.close()
        self.assertEqual(rows, [("r1",)])

    def test_safety_backup_failure_aborts_restore(self):
        backup_path = self.manager.create_backup()
        original = BackupManager.create_backup

        def failing(self, **kwargs):
            raise OSError("disk full")

        BackupManager.create_backup = failing
        try:
            with self.assertRaises(BackupValidationError):
                self.manager.restore_backup(backup_path)
        finally:
            BackupManager.create_backup = original
        # Bestehende Daten unverändert
        self.assertTrue(self.db_path.exists())


if __name__ == "__main__":
    unittest.main()
