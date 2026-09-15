import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from migrations import (
    CURRENT_SCHEMA_VERSION,
    MIGRATIONS,
    current_version,
    migrate,
)


class TestMigrations(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.db_path = str(self.tmp / "results.db")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_fresh_database_migrates_to_latest(self):
        version = migrate(self.db_path)
        self.assertEqual(version, CURRENT_SCHEMA_VERSION)
        with sqlite3.connect(self.db_path) as conn:
            tables = {row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        for table in ("results", "projects", "recipes", "result_versions",
                      "batch_jobs", "batch_items", "eval_suites", "eval_runs",
                      "schema_migrations"):
            self.assertIn(table, tables)

    def test_migrate_is_idempotent(self):
        migrate(self.db_path)
        self.assertEqual(migrate(self.db_path), CURRENT_SCHEMA_VERSION)
        with sqlite3.connect(self.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
        self.assertEqual(count, len(MIGRATIONS))

    def test_legacy_database_migrates_losslessly(self):
        # Simuliere eine Alt-Datenbank: nur results-Tabelle, kein Migrationssystem
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE results (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL,
                    analysis_type TEXT NOT NULL, source_type TEXT,
                    source_url TEXT, source_file_path TEXT, source_file_name TEXT,
                    content_preview TEXT, has_visualizations BOOLEAN,
                    has_exportable_data BOOLEAN, processing_time REAL,
                    model_used TEXT, tokens_used INTEGER, confidence_score REAL,
                    tags TEXT, created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL, json_file_path TEXT NOT NULL
                )
            """)
            conn.execute(
                "INSERT INTO results (id, title, analysis_type, created_at,"
                " updated_at, json_file_path) VALUES ('old1', 'Alt', 'text',"
                " '2024-01-01T00:00:00', '2024-01-01T00:00:00', 'results/old1.json')")
            conn.commit()

        self.assertEqual(current_version(self.db_path), 0)
        version = migrate(self.db_path)
        self.assertEqual(version, CURRENT_SCHEMA_VERSION)

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT title, is_favorite, project_id FROM results WHERE id='old1'"
            ).fetchone()
        self.assertEqual(row[0], "Alt")
        self.assertIn(row[1], (0, None))
        self.assertIsNone(row[2])

    def test_current_version_unknown_db(self):
        self.assertEqual(current_version(self.db_path), 0)


if __name__ == "__main__":
    unittest.main()
