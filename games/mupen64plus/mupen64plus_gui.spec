# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Mupen64Plus launch-options GUI.

Build with either::

    pyinstaller mupen64plus_gui.spec
    pyinstaller --onefile --windowed --name mupen64plus_gui src/gui.py
"""

block_cipher = None

a = Analysis(
    ['src/gui.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src/default_config.toml', '.'),
        ('src/default_profiles.toml', '.'),
    ],
    hiddenimports=['config', 'profile'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='mupen64plus_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
