# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-Spec für das KI Analysetool.

Erzeugt pro Plattform ein startbares Paket:
- macOS:   dist/KI_Analysetool.app (unsigned)
- Windows: dist/KI_Analysetool/KI_Analysetool.exe
- Linux:   dist/KI_Analysetool/KI_Analysetool

Build: `python build_app.py` (installiert PyInstaller bei Bedarf).
"""
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

datas = [
    ("HELP.md", "."),
    ("USER_GUIDE.md", "."),
    ("README.md", "."),
]
binaries = []
hiddenimports = []

# Optionale Drag-&-Drop-Erweiterung komplett mitnehmen (Binärbibliotheken
# und PyInstaller-Hook liegen im Paket).
try:
    _dnd = collect_all("tkinterdnd2")
    datas += _dnd[0]
    binaries += _dnd[1]
    hiddenimports += _dnd[2]
except Exception:
    pass

# Keyring-Backends werden je nach Plattform dynamisch geladen.
hiddenimports += collect_submodules("keyring.backends")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "pytest_cov"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="KI_Analysetool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="KI_Analysetool",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="KI_Analysetool.app",
        bundle_identifier="com.ki-analysetool.app",
        info_plist={
            "CFBundleName": "KI Analysetool",
            "CFBundleShortVersionString": "2.1.0",
            "NSHighResolutionCapable": True,
        },
    )
