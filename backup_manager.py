"""
Backup & Restore für das KI Analysetool.

Erstellt ZIP-Archive aus der SQLite-Datenbank (results.db) und dem
Ergebnis-Verzeichnis (results/) und stellt diese wieder her.

Härtung:
- Jedes Backup enthält ein manifest.json mit Formatversion und Metadaten.
- Restore validiert ZIP-Integrität und schützt gegen Zip-Slip
  (keine absoluten Pfade, keine "..", nur erlaubte Top-Level-Einträge).
- Vor dem Überschreiben wird automatisch ein Sicherungs-Backup des
  aktuellen Stands erstellt.
"""

import json
import logging
import re
import shutil
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Optional


BACKUP_MANIFEST_NAME = "manifest.json"
BACKUP_FORMAT_VERSION = 1
# Erlaubte Top-Level-Einträge im Archiv (Whitelist gegen unerwartete Inhalte).
_ALLOWED_TOP_LEVEL = frozenset({"results.db", "results", "config.ini", BACKUP_MANIFEST_NAME})
_SQLITE_MAGIC = b"SQLite format 3\x00"


class BackupValidationError(Exception):
    """Wird geworfen, wenn ein Backup-Archiv ungültig oder unsicher ist."""


def _is_safe_member(name: str) -> bool:
    """Prüft einen ZIP-Eintragsnamen gegen Zip-Slip und unerwartete Inhalte."""
    if not name or "\x00" in name:
        return False
    normalized = name.replace("\\", "/")
    if re.match(r"^[A-Za-z]:", normalized):
        return False
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        return False
    return path.parts[0] in _ALLOWED_TOP_LEVEL


class BackupManager:
    """Verwaltet Backup und Restore der Ergebnis-Datenbank und -Dateien."""

    def __init__(self, db_path: str = "results.db", results_dir: str = "results",
                 backup_dir: str = "backups"):
        self.db_path = Path(db_path)
        self.results_dir = Path(results_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, include_config: bool = False,
                      config_path: str = "config.ini",
                      name_suffix: str = "") -> str:
        """
        Erstellt ein ZIP-Backup aus results.db und results/.

        Args:
            include_config: Wenn True, wird config.ini (ohne API-Key) inkludiert.
            config_path: Pfad zur Konfigurationsdatei.
            name_suffix: Optionaler Namenszusatz (z. B. für Sicherungs-Backups
                vor einem Restore); verhindert Kollisionen mit regulären Backups.

        Returns:
            Pfad zur erstellten Backup-Datei.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if name_suffix:
            # Mikrosekunden verhindern Kollisionen mit Backups derselben Sekunde.
            timestamp += f"_{datetime.now().microsecond}"
        backup_file = self.backup_dir / f"ki_analysetool_backup_{timestamp}{name_suffix}.zip"
        members = []

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
                    members.append("results.db")
                finally:
                    if tmp_db.exists():
                        tmp_db.unlink()
            else:
                logging.warning("Keine results.db gefunden – Backup ohne Datenbank.")

            # Ergebnis-JSON-Dateien
            if self.results_dir.exists():
                for file_path in sorted(self.results_dir.rglob("*")):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.results_dir.parent)
                        zf.write(file_path, str(arcname))
                        members.append(str(arcname))

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
                members.append("config.ini")

            manifest = {
                "format_version": BACKUP_FORMAT_VERSION,
                "app": "KI_Analysetool",
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "includes_config": bool(include_config and "config.ini" in members),
                "file_count": len(members),
                "files": members,
            }
            zf.writestr(BACKUP_MANIFEST_NAME,
                        json.dumps(manifest, ensure_ascii=False, indent=2))

        logging.info(f"Backup erstellt: {backup_file}")
        return str(backup_file)

    def validate_backup(self, backup_file: str) -> dict:
        """Validiert ein Backup-Archiv ohne es zu extrahieren.

        Prüft ZIP-Integrität, Eintragssicherheit (Zip-Slip), Manifest und
        – falls vorhanden – den SQLite-Header der enthaltenen Datenbank.

        Returns:
            Report-Dict mit valid, errors, warnings und manifest.

        Raises:
            FileNotFoundError: wenn die Datei nicht existiert.
        """
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup-Datei nicht gefunden: {backup_file}")

        report = {"valid": True, "errors": [], "warnings": [], "manifest": None}

        try:
            with zipfile.ZipFile(backup_path, "r") as zf:
                if zf.testzip() is not None:
                    report["errors"].append("ZIP-Archiv ist beschädigt.")

                for info in zf.infolist():
                    if not _is_safe_member(info.filename):
                        report["errors"].append(
                            f"Unsicherer oder unerlaubter Archiveintrag: {info.filename}"
                        )

                manifest = None
                if BACKUP_MANIFEST_NAME in zf.namelist():
                    try:
                        manifest = json.loads(zf.read(BACKUP_MANIFEST_NAME).decode("utf-8"))
                        report["manifest"] = manifest
                        version = manifest.get("format_version", 0)
                        if not isinstance(version, int) or version > BACKUP_FORMAT_VERSION:
                            report["errors"].append(
                                f"Nicht unterstützte Backup-Formatversion: {version}"
                            )
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        report["errors"].append("Manifest ist beschädigt oder unlesbar.")
                else:
                    report["warnings"].append(
                        "Kein Manifest gefunden – Backup stammt vermutlich aus einer älteren Version."
                    )

                if "results.db" in zf.namelist():
                    with zf.open("results.db") as db_entry:
                        if db_entry.read(len(_SQLITE_MAGIC)) != _SQLITE_MAGIC:
                            report["errors"].append(
                                "results.db im Backup ist keine gültige SQLite-Datenbank."
                            )
                else:
                    report["warnings"].append("Backup enthält keine results.db.")
        except zipfile.BadZipFile:
            report["valid"] = False
            report["errors"].append("Die Datei ist kein gültiges ZIP-Archiv.")
            return report

        report["valid"] = not report["errors"]
        return report

    def restore_backup(self, backup_file: str, overwrite: bool = True,
                       create_safety_backup: bool = True) -> dict:
        """
        Stellt ein Backup wieder her.

        Args:
            backup_file: Pfad zur ZIP-Backup-Datei.
            overwrite: Wenn True, werden bestehende Dateien überschrieben.
            create_safety_backup: Wenn True, wird vor dem Überschreiben ein
                Sicherungs-Backup des aktuellen Stands erstellt.

        Returns:
            Dict mit safety_backup (Pfad oder None) und warnings.

        Raises:
            BackupValidationError: bei ungültigem oder unsicherem Archiv.
        """
        report = self.validate_backup(backup_file)
        if not report["valid"]:
            raise BackupValidationError(
                "Backup-Validierung fehlgeschlagen: " + "; ".join(report["errors"])
            )

        if not overwrite:
            # Prüfen, ob Zieldateien existieren
            if self.db_path.exists() or self.results_dir.exists():
                raise FileExistsError(
                    "Zieldateien existieren bereits. Setze overwrite=True zum Überschreiben."
                )

        # Sicherungs-Backup des aktuellen Stands, bevor überschrieben wird.
        safety_backup = None
        if create_safety_backup and (self.db_path.exists() or self.results_dir.exists()):
            try:
                safety_backup = self.create_backup(name_suffix="_sicherung")
            except Exception:
                logging.exception("Sicherungs-Backup vor Restore fehlgeschlagen")
                raise BackupValidationError(
                    "Sicherungs-Backup vor dem Restore konnte nicht erstellt werden. "
                    "Restore wurde abgebrochen, um Datenverlust zu vermeiden."
                )

        with zipfile.ZipFile(backup_file, "r") as zf:
            # Erst in temporäres Verzeichnis extrahieren, dann atomar verschieben
            tmp_dir = self.backup_dir / "_restore_tmp"
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
            tmp_dir.mkdir()

            try:
                # Nur geprüfte Einträge einzeln extrahieren (Zip-Slip-Schutz).
                for info in zf.infolist():
                    if not _is_safe_member(info.filename):
                        raise BackupValidationError(
                            f"Unsicherer Archiveintrag: {info.filename}"
                        )
                    normalized = info.filename.replace("\\", "/")
                    target = tmp_dir / normalized
                    resolved = target.resolve()
                    if not str(resolved).startswith(str(tmp_dir.resolve()) + "/"):
                        raise BackupValidationError(
                            f"Archiveintrag verlässt das Zielverzeichnis: {info.filename}"
                        )
                    if info.is_dir():
                        target.mkdir(parents=True, exist_ok=True)
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(info) as source, open(resolved, "wb") as dest:
                        shutil.copyfileobj(source, dest)

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
        return {"safety_backup": safety_backup, "warnings": report["warnings"]}

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
