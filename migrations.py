"""Versionierte SQLite-Schema-Migrationen für das KI Analysetool.

Die Datenbankversion wird in der Tabelle `schema_migrations` gehalten.
`migrate()` wendet ausstehende Migrationen in aufsteigender Reihenfolge an –
jede in einer eigenen Transaktion. Bestehende Datenbanken werden verlustfrei
fortgeschrieben: die Baseline-Migration ist idempotent und erzeugt exakt das
bisherige Schema, neuere Migrationen ergänzen Tabellen/Spalten.
"""

import sqlite3
from datetime import datetime
from typing import List, Tuple

SCHEMA_MIGRATIONS_TABLE = "schema_migrations"
CURRENT_SCHEMA_VERSION = 2


def _migration_1_baseline(conn: sqlite3.Connection):
    """Baseline: bisheriges results-Schema (idempotent für Altdatenbanken)."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
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
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON results(created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_type ON results(analysis_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_source_type ON results(source_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tags ON results(tags)")
    try:
        conn.execute("ALTER TABLE results ADD COLUMN is_favorite BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Spalte existiert bereits
    conn.execute("CREATE INDEX IF NOT EXISTS idx_is_favorite ON results(is_favorite)")


def _migration_2_projects_recipes_versions(conn: sqlite3.Connection):
    """M6: Projekte, Analyse-Rezepte und Ergebnis-Versionen."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            archived BOOLEAN DEFAULT 0,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
            source_type TEXT,
            prompt_template TEXT NOT NULL,
            model TEXT,
            follow_up_actions TEXT,
            export_format TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS result_versions (
            id TEXT PRIMARY KEY,
            result_id TEXT NOT NULL REFERENCES results(id) ON DELETE CASCADE,
            version_no INTEGER NOT NULL,
            content TEXT NOT NULL,
            note TEXT,
            created_at TIMESTAMP NOT NULL,
            UNIQUE(result_id, version_no)
        )
    """)
    try:
        conn.execute("ALTER TABLE results ADD COLUMN project_id TEXT REFERENCES projects(id)")
    except sqlite3.OperationalError:
        pass  # Spalte existiert bereits
    conn.execute("CREATE INDEX IF NOT EXISTS idx_results_project ON results(project_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_versions_result ON result_versions(result_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_recipes_project ON recipes(project_id)")


MIGRATIONS: List[Tuple[int, str, object]] = [
    (1, "Baseline-Schema (results)", _migration_1_baseline),
    (2, "Projekte, Rezepte, Ergebnisversionen", _migration_2_projects_recipes_versions),
]


def current_version(db_path: str) -> int:
    """Gibt die angewendete Schema-Version zurück (0 = keine Migrationen)."""
    with sqlite3.connect(db_path) as conn:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (SCHEMA_MIGRATIONS_TABLE,)
        ).fetchone()
        if not exists:
            return 0
        row = conn.execute(
            f"SELECT MAX(version) FROM {SCHEMA_MIGRATIONS_TABLE}"
        ).fetchone()
        return row[0] or 0


def migrate(db_path: str) -> int:
    """Wendet alle ausstehenden Migrationen an.

    Args:
        db_path: Pfad zur SQLite-Datenbank.

    Returns:
        Die Schema-Version nach der Migration.
    """
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA_MIGRATIONS_TABLE} (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TIMESTAMP NOT NULL
            )
        """)
        conn.commit()
        applied = {
            row[0] for row in conn.execute(
                f"SELECT version FROM {SCHEMA_MIGRATIONS_TABLE}"
            ).fetchall()
        }
        for version, description, migration in MIGRATIONS:
            if version in applied:
                continue
            try:
                migration(conn)
                conn.execute(
                    f"INSERT INTO {SCHEMA_MIGRATIONS_TABLE} (version, description, applied_at)"
                    " VALUES (?, ?, ?)",
                    (version, description, datetime.now().isoformat())
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    return current_version(db_path)
