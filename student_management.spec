# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules


hiddenimports = collect_submodules("uvicorn") + collect_submodules("webapp")

a = Analysis(
    ["desktop_launcher.py"],
    pathex=[],
    binaries=[],
    datas=[("webapp/templates", "webapp/templates")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="StudentAnalytics",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
