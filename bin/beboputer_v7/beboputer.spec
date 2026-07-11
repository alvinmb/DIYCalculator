# -*- mode: python ; coding: utf-8 -*-
#
# beboputer.spec — PyInstaller build recipe
# ─────────────────────────────────────────
# Run from the project root (Bebop_python/) with:
#
#   pyinstaller beboputer.spec
#
# Output lands in  dist/Beboputer/
#
# Requirements (install once per machine):
#   pip install pyinstaller pyqt5
#
# Build on each target platform natively:
#   Windows  →  dist/Beboputer/Beboputer.exe  (+ support folder)
#   macOS    →  dist/Beboputer.app
#   Linux    →  dist/Beboputer/Beboputer      (+ support folder)

block_cipher = None

import os
# SPECPATH is injected by PyInstaller = the folder containing this .spec file
# (bin/beboputer_v7/). Project root is two levels up. Resolving it this way
# means the build works regardless of where the repo is checked out.
_root = os.path.normpath(os.path.join(SPECPATH, '..', '..'))

a = Analysis(
    # ── entry point ──────────────────────────────────────────────────────────
    [os.path.join(_root, 'bin', 'run_beboputer_v7.py')],

    # ── import paths — 'bin/' must be on sys.path so the package is found ───
    pathex=[os.path.join(_root, 'bin')],

    binaries=[],

    # ── data files ───────────────────────────────────────────────────────────
    # Tuples are (source_on_disk, dest_inside_bundle).
    # All destinations are relative to sys._MEIPASS (the bundle root).
    datas=[
        (os.path.join(_root, 'BITMAPS'),                    'BITMAPS'),
        (os.path.join(_root, 'Config'),                     'Config'),
        (os.path.join(_root, 'Data'),                       'Data'),
        (os.path.join(_root, 'WorkInProgress'),              'WorkInProgress'),
        (os.path.join(_root, 'databook'),                   'databook'),
        (os.path.join(_root, 'tutorial'),                   'tutorial'),
        (os.path.join(_root, 'bin', 'beboputer_v7_help.html'), '.'),
    ],

    hiddenimports=[
        # PyQt5 plugins that PyInstaller sometimes misses on certain platforms
        'PyQt5.sip',
        'PyQt5.QtPrintSupport',
    ],

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
    [],
    exclude_binaries=True,
    name='Beboputer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no terminal window on Windows/macOS
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(SPECPATH, 'beboputer.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Beboputer',
)

# ── macOS: wrap everything in a .app bundle ───────────────────────────────────
import sys
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Beboputer.app',
        # icon='assets/beboputer.icns',  # uncomment and supply an .icns file
        bundle_identifier='com.beboputer.app',
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleShortVersionString': '7.0',
        },
    )
