"""Plattformübergreifender Build des KI Analysetools mit PyInstaller.

Verwendung:
    .venv/bin/python build_app.py

Voraussetzung: `pip install -r requirements-build.txt` (enthält PyInstaller).
Ergebnis liegt in `dist/`:
- macOS:   dist/KI_Analysetool.app
- Windows: dist/KI_Analysetool/KI_Analysetool.exe (+ ZIP)
- Linux:   dist/KI_Analysetool/KI_Analysetool (+ ZIP)

Optionale Signierung (nur aktiv, wenn die Umgebungsvariablen gesetzt sind):
- macOS:   CODESIGN_IDENTITY (z. B. "Developer ID Application: Name (TEAMID)")
           Notarisierung: NOTARY_APPLE_ID, NOTARY_TEAM_ID, NOTARY_PASSWORD
- Windows: SIGNTOOL_CERT (PFX-Pfad), SIGNTOOL_PASSWORD
Ohne diese Variablen bleibt der Build unsigned – ein deutlicher Hinweis
wird ausgegeben.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


SPEC_FILE = Path(__file__).parent / "ki_analysetool.spec"
APP_NAME = "KI_Analysetool"


def _run(args, description: str) -> bool:
    print(f"→ {description}")
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print(f"✗ {description} fehlgeschlagen.")
        return False
    print(f"✓ {description}")
    return True


def sign_macos(app_path: Path) -> bool:
    """Signiert die .app und notarisiert sie, wenn Credentials vorhanden sind."""
    identity = os.environ.get("CODESIGN_IDENTITY")
    if not identity:
        print("ℹ Kein CODESIGN_IDENTITY gesetzt – macOS-Build bleibt unsigned.")
        return True
    if not _run(
        ["codesign", "--deep", "--force", "--options", "runtime",
         "--sign", identity, str(app_path)],
        "codesign (hardened runtime)"):
        return False

    apple_id = os.environ.get("NOTARY_APPLE_ID")
    team_id = os.environ.get("NOTARY_TEAM_ID")
    password = os.environ.get("NOTARY_PASSWORD")
    if not (apple_id and team_id and password):
        print("ℹ Keine Notary-Credentials – Notarisierung übersprungen.")
        return True

    zip_path = app_path.with_suffix(".zip")
    subprocess.run(["ditto", "-c", "-k", "--keepParent",
                    str(app_path), str(zip_path)], check=True)
    try:
        if not _run(
            ["xcrun", "notarytool", "submit", str(zip_path),
             "--apple-id", apple_id, "--team-id", team_id,
             "--password", password, "--wait"],
            "Notarisierung"):
            return False
        return _run(["xcrun", "stapler", "staple", str(app_path)],
                    "Staple des Notarization-Tickets")
    finally:
        zip_path.unlink(missing_ok=True)


def sign_windows(exe_path: Path) -> bool:
    """Signiert die .exe mit signtool, wenn ein Zertifikat konfiguriert ist."""
    cert = os.environ.get("SIGNTOOL_CERT")
    password = os.environ.get("SIGNTOOL_PASSWORD", "")
    if not cert:
        print("ℹ Kein SIGNTOOL_CERT gesetzt – Windows-Build bleibt unsigned.")
        return True
    args = ["signtool", "sign", "/fd", "sha256", "/f", cert]
    if password:
        args += ["/p", password]
    args += ["/t", "http://timestamp.digicert.com", str(exe_path)]
    return _run(args, "signtool sign")


def main() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller fehlt. Installieren mit: "
              "pip install -r requirements-build.txt")
        return 1

    print(f"Baue {APP_NAME} für {sys.platform} …")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller",
         "--clean", "--noconfirm", str(SPEC_FILE)],
    )
    if result.returncode != 0:
        print("Build fehlgeschlagen.")
        return result.returncode

    dist = Path("dist")
    if sys.platform == "darwin":
        artifact = dist / f"{APP_NAME}.app"
        if not sign_macos(artifact):
            return 1
        print(f"Fertig: {artifact}")
        print("Hinweis: unsigned Builds benötigen Rechtsklick → Öffnen.")
    else:
        suffix = ".exe" if sys.platform == "win32" else ""
        artifact_dir = dist / APP_NAME
        binary = artifact_dir / f"{APP_NAME}{suffix}"
        if sys.platform == "win32" and not sign_windows(binary):
            return 1
        archive = shutil.make_archive(
            str(dist / f"{APP_NAME}-{sys.platform}"), "zip", artifact_dir)
        print(f"Fertig: {binary}")
        print(f"Verteilbares Archiv: {archive}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
