# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.win32 import winutils

winutils.set_exe_build_timestamp = lambda *args, **kwargs: None
winutils.update_exe_pe_checksum = lambda *args, **kwargs: None

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=[("builtin_songs", "builtin_songs"), ("assets/app_icon.png", "assets")],
    hiddenimports=[],
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
    name="JianpuPlayerNext-v1.0.0-beta.41",
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
    uac_admin=True,
    icon=["assets/app_icon.ico"],
)

