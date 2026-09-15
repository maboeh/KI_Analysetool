"""End-to-End-Upgrade-Tests: alte Datenbestände → aktuelles Schema (M11).

Simuliert eine Alt-Datenbank aus der Zeit vor den Migrationen sowie einen
App-Neustart mitten in einem laufenden Batch-Job.
"""

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from migrations import CURRENT_SCHEMA_VERSION, current_version, migrate


LEGACY_RESULTS_DDL = """
CREATE TABLE results (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    analysis_type TEXT NOT NULL,
    source_type TEXT,
    source_url TEXT,
    source_file_path TEXT,
    source_file_name TEXT,
    content_preview TEXT,
    has_visualizations BOOLEAN DEFAULT FALSE,
    has_exportable_data BOOLEAN DEFAULT FALSE,
    processing_time REAL,
    model_used TEXT,
    tokens_used INTEGER,
    confidence_score REAL,
    tags TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    json_file_path TEXT NOT NULL
)
"""


class TestLegacyDatabaseUpgrade(unittest.TestCase):
    """Eine Alt-DB ohne Migrationstabelle muss verlustfrei migrieren."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "results.db")
        self.results_dir = Path(self.tmpdir.name) / "results"
        self.results_dir.mkdir()

        # Altes Schema: keine schema_migrations, keine is_favorite/project_id
        conn = sqlite3.connect(self.db_path)
        conn.execute(LEGACY_RESULTS_DDL)
        json_path = str(self.results_dir / "legacy-1.json")
        conn.execute("""
            INSERT INTO results (id, title, analysis_type, created_at,
                                 updated_at, json_file_path)
            VALUES ('legacy-1', 'Altes Ergebnis', 'text', '2024-01-01',
                    '2024-01-01', ?)
        """, (json_path,))
        conn.commit()
        conn.close()

        (self.results_dir / "legacy-1.json").write_text(json.dumps({
            "id": "legacy-1",
            "content": "Alter Inhalt",
            "source_info": None,
            "extracted_data": {},
            "visualizations": [],
            "follow_up_actions": [],
            "metadata": {"analysis_type": "text"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }), encoding="utf-8")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_legacy_db_migrates_to_current_version(self):
        self.assertEqual(current_version(self.db_path), 0)
        version = migrate(self.db_path)
        self.assertEqual(version, CURRENT_SCHEMA_VERSION)
        # M13: Evaluationssuite-Tabellen müssen nach Migration existieren
        conn = sqlite3.connect(self.db_path)
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        conn.close()
        self.assertIn("eval_suites", tables)
        self.assertIn("eval_runs", tables)

    def test_legacy_row_survives_migration(self):
        migrate(self.db_path)
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT title, is_favorite, project_id FROM results WHERE id='legacy-1'"
        ).fetchone()
        conn.close()
        self.assertEqual(row[0], "Altes Ergebnis")
        self.assertEqual(row[1], 0)
        self.assertIsNone(row[2])

    def test_results_manager_opens_migrated_db(self):
        from results_manager import ResultsManager
        manager = ResultsManager(db_path=self.db_path,
                                 results_dir=str(self.results_dir))
        result = manager.load_result("legacy-1")
        self.assertIsNotNone(result)
        self.assertEqual(result.content, "Alter Inhalt")

    def test_new_entities_work_after_upgrade(self):
        from projects import ProjectManager
        from results_manager import ResultsManager
        manager = ResultsManager(db_path=self.db_path,
                                 results_dir=str(self.results_dir))
        projects = ProjectManager(self.db_path)
        project = projects.create_project("Altbestand")
        projects.assign_result("legacy-1", project.id)
        self.assertEqual(projects.get_project_result_ids(project.id), ["legacy-1"])


class TestBatchResumeAfterRestart(unittest.TestCase):
    """Unterbrochene Jobs werden nach 'Neustart' korrekt fortgesetzt."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "results.db")
        migrate(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_running_items_reset_to_pending_on_restart(self):
        from batch_queue import BatchQueue
        queue1 = BatchQueue(self.db_path)
        job_id = queue1.create_job("Job", prompt="p", items=[
            {"source": "a.txt"}, {"source": "b.txt"}])
        # Simuliere Absturz: Item wird als running markiert, App beendet sich.
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE batch_items SET status='running' "
                     "WHERE job_id=? AND position=0", (job_id,))
        conn.execute("UPDATE batch_jobs SET status='running' WHERE id=?", (job_id,))
        conn.commit()
        conn.close()

        # „Neustart": neue Queue-Instanz auf derselben DB
        queue2 = BatchQueue(self.db_path)
        items = queue2.get_items(job_id)
        self.assertTrue(all(i.status == "pending" for i in items))

    def test_done_items_survive_restart(self):
        from batch_queue import BatchQueue
        queue1 = BatchQueue(self.db_path)
        job_id = queue1.create_job("Job", prompt="p",
                                   items=[{"source": "a.txt"}])
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE batch_items SET status='done', result_id='r1' "
                     "WHERE job_id=?", (job_id,))
        conn.commit()
        conn.close()

        queue2 = BatchQueue(self.db_path)
        items = queue2.get_items(job_id)
        self.assertEqual(items[0].status, "done")
        self.assertEqual(items[0].result_id, "r1")


if __name__ == "__main__":
    unittest.main()
