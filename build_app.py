"""Plattformübergreifender Build des KI Analysetools mit PyInstaller.

Verwendung:
    .venv/bin/python build_app.py

Voraussetzung: `pip install -r requirements-build.txt` (enthält PyInstaller).
Ergebnis liegt in `dist/`:
- macOS:   dist/KI_Analysetool.app (unsigned; Gatekeeper-Hinweis beim ersten Start)
- Windows: dist/KI_Analysetool/KI_Analysetool.exe
- Linux:   dist/KI_Analysetool/KI_Analysetool
"""

import shutil
import subprocess
import sys
from pathlib import Path


SPEC_FILE = Path(__file__).parent / "ki_analysetool.spec"


def main() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller fehlt. Installieren mit: "
              "pip install -r requirements-build.txt")
        return 1

    print(f"Baue KI_Analysetool für {sys.platform} …")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller",
         "--clean", "--noconfirm", str(SPEC_FILE)],
    )
    if result.returncode != 0:
        print("Build fehlgeschlagen.")
        return result.returncode

    dist = Path("dist")
    if sys.platform == "darwin":
        artifact = dist / "KI_Analysetool.app"
        print(f"Fertig: {artifact}")
        print("Hinweis: unsigned – beim ersten Start Rechtsklick → Öffnen.")
    else:
        artifact = dist / "KI_Analysetool"
        suffix = ".exe" if sys.platform == "win32" else ""
        binary = artifact / f"KI_Analysetool{suffix}"
        # ZIP für einfache Verteilung
        archive = shutil.make_archive(
            str(dist / f"KI_Analysetool-{sys.platform}"), "zip", artifact)
        print(f"Fertig: {binary}")
        print(f"Verteilbares Archiv: {archive}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
