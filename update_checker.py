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
from dataclasses import dataclass
from typing import Optional, Tuple
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
    )
