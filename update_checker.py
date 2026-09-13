"""Update-Prüfung gegen GitHub-Releases (opt-in, keine Telemetrie).

Die Prüfung läuft ausschließlich auf Benutzeranforderung oder wenn der Nutzer
„Update-Check beim Start" explizit aktiviert hat. Es wird nur ein GET-Request
auf die öffentliche Releases-API gesendet; es werden keine Nutzungsdaten
übertragen. Die Installation erfolgt bewusst NICHT automatisch – der Nutzer
lädt die neue Version selbst von der Release-Seite herunter.
"""

import json
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

REPO = "maboeh/KI_Analysetool"
RELEASES_API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases/latest"


@dataclass(frozen=True)
class UpdateInfo:
    """Ergebnis der Update-Prüfung."""

    current_version: str
    latest_version: Optional[str]
    update_available: bool
    release_url: str = RELEASES_PAGE
    release_notes: str = ""
    assets: List[dict] = field(default_factory=list)
    error: Optional[str] = None


def parse_version(version: str) -> Tuple[int, ...]:
    """Parst 'v2.1.0' oder '2.1.0' in ein vergleichbares Tupel."""
    parts = re.findall(r"\d+", version or "")
    return tuple(int(p) for p in parts[:3]) if parts else (0,)


def check_for_update(current_version: str, timeout: float = 5.0) -> UpdateInfo:
    """Fragt die neueste Release-Version bei GitHub ab.

    Args:
        current_version: installierte Version (z. B. __version__ aus main.py).
        timeout: Netzwerk-Timeout in Sekunden.

    Returns:
        UpdateInfo; bei Netzwerkfehlern ist error gesetzt und
        update_available False.
    """
    try:
        request = Request(
            RELEASES_API,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "KI_Analysetool-UpdateCheck",
            },
        )
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        logger.info("Update-Prüfung fehlgeschlagen: %s", exc)
        return UpdateInfo(
            current_version=current_version,
            latest_version=None,
            update_available=False,
            error="Update-Prüfung nicht möglich (keine Verbindung zu GitHub).",
        )

    latest = str(payload.get("tag_name", "")).lstrip("v")
    if not latest:
        return UpdateInfo(
            current_version=current_version,
            latest_version=None,
            update_available=False,
            error="Keine Release-Information gefunden.",
        )

    return UpdateInfo(
        current_version=current_version,
        latest_version=latest,
        update_available=parse_version(latest) > parse_version(current_version),
        release_url=payload.get("html_url") or RELEASES_PAGE,
        release_notes=(payload.get("body") or "")[:4000],
        assets=[
            {"name": a.get("name", ""),
             "url": a.get("browser_download_url", ""),
             "size": a.get("size", 0)}
            for a in payload.get("assets", [])
            if a.get("browser_download_url")
        ],
    )


def pick_platform_asset(info: UpdateInfo,
                        platform: Optional[str] = None) -> Optional[dict]:
    """Wählt das Asset für die aktuelle Plattform aus.

    Erwartete Namensmuster aus dem Build-Workflow:
    KI_Analysetool-macos(.app/.zip), KI_Analysetool-Windows.zip,
    KI_Analysetool-Linux.zip.
    """
    platform = platform or sys.platform
    needles = {
        "darwin": ("macos", "darwin", "mac"),
        "win32": ("windows", "win"),
        "linux": ("linux",),
    }.get(platform, (platform,))
    for needle in needles:
        for asset in info.assets:
            if needle in asset["name"].lower():
                return asset
    return None


def download_release_asset(asset: dict, dest_dir: Optional[Path] = None,
                           timeout: float = 30.0,
                           progress=None) -> Optional[Path]:
    """Lädt ein Release-Asset in den Zielordner (Standard: ~/Downloads).

    Streamt den Download; bei Fehlern wird eine unvollständige Datei
    wieder entfernt und None zurückgegeben.
    """
    url = asset.get("url")
    name = asset.get("name") or "download"
    if not url:
        return None
    dest_dir = Path(dest_dir or Path.home() / "Downloads")
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / name
    try:
        request = Request(url, headers={"User-Agent": "KI_Analysetool-UpdateCheck"})
        with urlopen(request, timeout=timeout) as response, \
             open(dest, "wb") as out:
            total = int(response.headers.get("Content-Length") or 0)
            received = 0
            while True:
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                received += len(chunk)
                if progress:
                    try:
                        progress(received, total)
                    except Exception:
                        pass
        return dest
    except Exception:
        logger.info("Release-Download fehlgeschlagen: %s", url, exc_info=True)
        dest.unlink(missing_ok=True)
        return None


def open_in_file_manager(path: Path) -> bool:
    """Öffnet den Ordner der heruntergeladenen Datei im Dateimanager."""
    import subprocess
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(path)])
        elif sys.platform == "win32":
            subprocess.Popen(["explorer", "/select,", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path.parent)])
        return True
    except Exception:
        logger.info("Dateimanager konnte nicht geöffnet werden", exc_info=True)
        return False
