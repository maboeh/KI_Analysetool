"""
Backup & Restore für das KI Analysetool.

Erstellt ZIP-Archive aus der SQLite-Datenbank (results.db) und dem
Ergebnis-Verzeichnis (results/) und stellt diese wieder her.
"""

import os
import shutil
import zipfile
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


class BackupManager:
    """Verwaltet Backup und Restore der Ergebnis-Datenbank und -Dateien."""

    def __init__(self, db_path: str = "results.db", results_dir: str = "results",
                 backup_dir: str = "backups"):
        self.db_path = Path(db_path)
        self.results_dir = Path(results_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, include_config: bool = False,
                      config_path: str = "config.ini") -> str:
        """
        Erstellt ein ZIP-Backup aus results.db und results/.

        Args:
            include_config: Wenn True, wird config.ini (ohne API-Key) inkludiert.
            config_path: Pfad zur Konfigurationsdatei.

        Returns:
            Pfad zur erstellten Backup-Datei.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"ki_analysetool_backup_{timestamp}.zip"

        with zipfile.ZipFile(backup_file, "w", zipfile.ZIP_DEFLATED) as zf:
            # SQLite-Datenbank
            if self.db_path.exists():
                # Bei laufender DB: sichere Kopie ziehen, um Corruption zu vermeiden
                tmp_db = self.backup_dir / "_tmp_backup.db"
                try:
                    conn = sqlite3.connect(str(self.db_path))
                    conn.backup(sqlite3.connect(str(tmp_db)))
                    conn.close()
                    zf.write(tmp_db, "results.db")
                finally:
                    if tmp_db.exists():
                        tmp_db.unlink()
            else:
                logging.warning("Keine results.db gefunden – Backup ohne Datenbank.")

            # Ergebnis-JSON-Dateien
            if self.results_dir.exists():
                for file_path in self.results_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.results_dir.parent)
                        zf.write(file_path, arcname)

            # Konfiguration (sanitized – API-Key wird entfernt)
            if include_config and Path(config_path).exists():
                import configparser
                config = configparser.ConfigParser()
                config.read(config_path)
                # API-Key entfernen
                if 'API' in config:
                    for key_name in ('OpenAI_Key', 'openai_key', 'openai_api_key'):
                        if key_name in config['API']:
                            del config['API'][key_name]
                sanitized_path = self.backup_dir / "_config_sanitized.ini"
                with open(sanitized_path, "w", encoding="utf-8") as f:
                    config.write(f)
                zf.write(sanitized_path, "config.ini")
                sanitized_path.unlink()

        logging.info(f"Backup erstellt: {backup_file}")
        return str(backup_file)

    def restore_backup(self, backup_file: str, overwrite: bool = True) -> None:
        """
        Stellt ein Backup wieder her.

        Args:
            backup_file: Pfad zur ZIP-Backup-Datei.
            overwrite: Wenn True, werden bestehende Dateien überschrieben.
        """
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup-Datei nicht gefunden: {backup_file}")

        if not overwrite:
            # Prüfen, ob Zieldateien existieren
            if self.db_path.exists() or self.results_dir.exists():
                raise FileExistsError(
                    "Zieldateien existieren bereits. Setze overwrite=True zum Überschreiben."
                )

        with zipfile.ZipFile(backup_path, "r") as zf:
            # Erst in temporäres Verzeichnis extrahieren, dann atomar verschieben
            tmp_dir = self.backup_dir / "_restore_tmp"
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
            tmp_dir.mkdir()

            try:
                zf.extractall(tmp_dir)

                # Datenbank wiederherstellen
                tmp_db = tmp_dir / "results.db"
                if tmp_db.exists():
                    if self.db_path.exists():
                        self.db_path.unlink()
                    shutil.move(str(tmp_db), str(self.db_path))

                # Ergebnis-Verzeichnis wiederherstellen
                tmp_results = tmp_dir / "results"
                if tmp_results.exists():
                    if self.results_dir.exists():
                        shutil.rmtree(self.results_dir)
                    shutil.move(str(tmp_results), str(self.results_dir))
            finally:
                if tmp_dir.exists():
                    shutil.rmtree(tmp_dir)

        logging.info(f"Backup wiederhergestellt aus: {backup_file}")

    def list_backups(self):
        """Listet alle verfügbaren Backups auf."""
        backups = []
        for f in self.backup_dir.glob("ki_analysetool_backup_*.zip"):
            stat = f.stat()
            backups.append({
                "path": str(f),
                "name": f.name,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M"),
            })
        backups.sort(key=lambda b: b["name"], reverse=True)
        return backups
