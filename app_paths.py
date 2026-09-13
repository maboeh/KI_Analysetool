"""Pfad-Helfer für Entwicklungs- und PyInstaller-Betrieb (M10).

- `resource_path`: gebündelte Dateien (Doku, Assets). Im Frozen-Build liegen
  sie in `sys._MEIPASS`, in der Entwicklung neben dem Quellcode.
- `get_data_dir`: schreibbare Ablage für results.db, results/, logs/ und
  config.ini. Im Frozen-Build ein plattformübliches Benutzerverzeichnis,
  in der Entwicklung das Arbeitsverzeichnis.
"""

import os
import sys
from pathlib import Path

APP_NAME = "KI_Analysetool"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_path(name: str) -> Path:
    """Pfad zu einer gebündelten Nur-Lese-Datei."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS")) / name
    return Path(__file__).resolve().parent / name


def get_data_dir() -> Path:
    """Schreibbares Datenverzeichnis der App (wird angelegt)."""
    if is_frozen():
        if sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support"
        elif sys.platform == "win32":
            base = Path(os.environ.get(
                "APPDATA", Path.home() / "AppData" / "Roaming"))
        else:
            base = Path(os.environ.get(
                "XDG_DATA_HOME", Path.home() / ".local" / "share"))
        path = base / APP_NAME
    else:
        path = Path.cwd()
    path.mkdir(parents=True, exist_ok=True)
    return path
