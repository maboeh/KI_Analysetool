"""Projekt-Verwaltung für das KI Analysetool.

Bündelt Ergebnisse und Rezepte in benannten Arbeitsräumen. Projekte können
archiviert werden; beim Löschen bleiben die zugeordneten Ergebnisse erhalten
(die Zuordnung wird nur aufgehoben).
"""

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    description: str
    archived: bool
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def _from_row(row) -> "Project":
        return Project(
            id=row[0],
            name=row[1],
            description=row[2] or "",
            archived=bool(row[3]),
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5]),
        )


class ProjectManager:
    """CRUD und Zuordnung von Ergebnissen zu Projekten."""

    _COLUMNS = "id, name, description, archived, created_at, updated_at"

    def __init__(self, db_path: str = "results.db"):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create_project(self, name: str, description: str = "") -> Project:
        name = (name or "").strip()
        if not name:
            raise ValueError("Projektname darf nicht leer sein.")
        project = Project(
            id=str(uuid.uuid4()),
            name=name,
            description=description or "",
            archived=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, description, archived, created_at, updated_at)"
                " VALUES (?, ?, ?, 0, ?, ?)",
                (project.id, project.name, project.description,
                 project.created_at.isoformat(), project.updated_at.isoformat())
            )
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT {self._COLUMNS} FROM projects WHERE id = ?",
                (project_id,)
            ).fetchone()
        return Project._from_row(row) if row else None

    def list_projects(self, include_archived: bool = False) -> List[Project]:
        query = f"SELECT {self._COLUMNS} FROM projects"
        if not include_archived:
            query += " WHERE archived = 0"
        query += " ORDER BY name COLLATE NOCASE"
        with self._connect() as conn:
            return [Project._from_row(row) for row in conn.execute(query).fetchall()]

    def update_project(self, project_id: str, name: Optional[str] = None,
                       description: Optional[str] = None) -> bool:
        updates = []
        params = []
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("Projektname darf nicht leer sein.")
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if not updates:
            return False
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(project_id)
        with self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE projects SET {', '.join(updates)} WHERE id = ?", params)
            return cursor.rowcount > 0

    def set_archived(self, project_id: str, archived: bool = True) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE projects SET archived = ?, updated_at = ? WHERE id = ?",
                (1 if archived else 0, datetime.now().isoformat(), project_id)
            )
            return cursor.rowcount > 0

    def delete_project(self, project_id: str) -> bool:
        """Löscht ein Projekt. Zugeordnete Ergebnisse bleiben erhalten."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE results SET project_id = NULL WHERE project_id = ?",
                (project_id,)
            )
            cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return cursor.rowcount > 0

    def assign_result(self, result_id: str, project_id: Optional[str]) -> bool:
        """Ordnet ein Ergebnis einem Projekt zu (None = Zuordnung entfernen)."""
        if project_id is not None and self.get_project(project_id) is None:
            raise ValueError("Projekt nicht gefunden.")
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE results SET project_id = ?, updated_at = ? WHERE id = ?",
                (project_id, datetime.now().isoformat(), result_id)
            )
            return cursor.rowcount > 0

    def get_project_result_ids(self, project_id: str) -> List[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id FROM results WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,)
            ).fetchall()
        return [row[0] for row in rows]
