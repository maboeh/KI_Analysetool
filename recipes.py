"""Analyse-Rezepte für das KI Analysetool.

Ein Rezept bündelt Quelltyp, Prompt-Vorlage, Modell, geplante Folgeaktionen
und Exportformat zu einer wiederverwendbaren Analyse-Konfiguration. Rezepte
können optional einem Projekt zugeordnet werden.
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class AnalysisRecipe:
    id: str
    name: str
    description: str
    source_type: str
    prompt_template: str
    model: Optional[str]
    follow_up_actions: List[str] = field(default_factory=list)
    export_format: Optional[str] = None
    project_id: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

    @staticmethod
    def _from_row(row) -> "AnalysisRecipe":
        try:
            follow_ups = json.loads(row[7]) if row[7] else []
        except (json.JSONDecodeError, TypeError):
            follow_ups = []
        return AnalysisRecipe(
            id=row[0],
            name=row[1],
            description=row[2] or "",
            project_id=row[3],
            source_type=row[4] or "default",
            prompt_template=row[5],
            model=row[6],
            follow_up_actions=follow_ups,
            export_format=row[8],
            created_at=datetime.fromisoformat(row[9]),
            updated_at=datetime.fromisoformat(row[10]),
        )


class RecipeManager:
    """CRUD für Analyse-Rezepte."""

    _COLUMNS = ("id, name, description, project_id, source_type, prompt_template,"
                " model, follow_up_actions, export_format, created_at, updated_at")

    def __init__(self, db_path: str = "results.db"):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create_recipe(self, name: str, prompt_template: str,
                      source_type: str = "default",
                      description: str = "",
                      model: Optional[str] = None,
                      follow_up_actions: Optional[List[str]] = None,
                      export_format: Optional[str] = None,
                      project_id: Optional[str] = None) -> AnalysisRecipe:
        name = (name or "").strip()
        if not name:
            raise ValueError("Rezeptname darf nicht leer sein.")
        if not (prompt_template or "").strip():
            raise ValueError("Prompt-Vorlage darf nicht leer sein.")
        recipe = AnalysisRecipe(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            source_type=source_type,
            prompt_template=prompt_template,
            model=model,
            follow_up_actions=follow_up_actions or [],
            export_format=export_format,
            project_id=project_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO recipes (id, name, description, project_id, source_type,"
                " prompt_template, model, follow_up_actions, export_format,"
                " created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (recipe.id, recipe.name, recipe.description, recipe.project_id,
                 recipe.source_type, recipe.prompt_template, recipe.model,
                 json.dumps(recipe.follow_up_actions), recipe.export_format,
                 recipe.created_at.isoformat(), recipe.updated_at.isoformat())
            )
        return recipe

    def get_recipe(self, recipe_id: str) -> Optional[AnalysisRecipe]:
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT {self._COLUMNS} FROM recipes WHERE id = ?",
                (recipe_id,)
            ).fetchone()
        return AnalysisRecipe._from_row(row) if row else None

    def list_recipes(self, project_id: Optional[str] = None) -> List[AnalysisRecipe]:
        query = f"SELECT {self._COLUMNS} FROM recipes"
        params = []
        if project_id:
            query += " WHERE project_id = ? OR project_id IS NULL"
            params.append(project_id)
        query += " ORDER BY name COLLATE NOCASE"
        with self._connect() as conn:
            return [AnalysisRecipe._from_row(row)
                    for row in conn.execute(query, params).fetchall()]

    def update_recipe(self, recipe_id: str, **fields) -> bool:
        allowed = {"name", "description", "project_id", "source_type",
                   "prompt_template", "model", "follow_up_actions", "export_format"}
        updates = []
        params = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            if key == "name" and not (value or "").strip():
                raise ValueError("Rezeptname darf nicht leer sein.")
            if key == "prompt_template" and not (value or "").strip():
                raise ValueError("Prompt-Vorlage darf nicht leer sein.")
            if key == "follow_up_actions":
                value = json.dumps(value or [])
            updates.append(f"{key} = ?")
            params.append(value)
        if not updates:
            return False
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(recipe_id)
        with self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE recipes SET {', '.join(updates)} WHERE id = ?", params)
            return cursor.rowcount > 0

    def delete_recipe(self, recipe_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
            return cursor.rowcount > 0
