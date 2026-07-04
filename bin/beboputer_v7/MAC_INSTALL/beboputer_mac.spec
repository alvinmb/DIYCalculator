# -*- mode: python ; coding: utf-8 -*-
#
# beboputer_mac.spec — PyInstaller build recipe for macOS
# ────────────────────────────────────────────────────────
# Run from the project root (Bebop_python/) with:
#
#   pyinstaller bin/beboputer_v7/MAC_INSTALL/beboputer_mac.spec --noconfirm
#
# Output: dist/Beboputer.app
#
# Requirements (install once):
#   pip3 install pyinstaller pyqt5
#
# To also create a .dmg, run build_mac.sh instead.

block_cipher = None

import os, sys

# ── Resolve project root relative to this spec file ──────────────────────────
# This spec lives at:  <project_root>/bin/beboputer_v7/MAC_INSTALL/
_here   = os.path.dirname(os.path.abspath(SPEC))
_root   = os.path.normpath(os.path.join(_here, '..', '..', '..'))

a = Analysis(
    [os.path.join(_root, 'bin', 'run_beboputer_v7.py')],

    pathex=[os.path.join(_root, 'bin')],

    binaries=[],

    datas=[
        (os.path.join(_root, 'BITMAPS'),                       'BITMAPS'),
        (os.path.join(_root, 'Config'),                        'Config'),
        (os.path.join(_root, 'bin', 'beboputer_v7_help.html'), '.'),
    ],

    hiddenimports=[
        'PyQt5.sip',
        'PyQt5.QtPrintSupport',
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    strip=False,
    upx=True,
    console=False,           # no terminal window
    target_arch=None,        # 'arm64' | 'x86_64' | None (native)
    codesign_identity=None,  # set to your Developer ID to sign
    entitlements_file=None,
    # icon='MAC_INSTALL/beboputer.icns',   # uncomment + supply .icns
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

app = BUNDLE(
    coll,
    name='Beboputer.app',
    # icon='MAC_INSTALL/beboputer.icns',   # uncomment + supply .icns
    bundle_identifier='com.beboputer.app',
    info_plist={
        'CFBundleDisplayName':        'PY-DIYCALCULATOR',
        'CFBundleShortVersionString': '7.0.0',
        'CFBundleVersion':            '7.0.0',
        'NSHighResolutionCapable':    True,
        'NSHumanReadableCopyright':   'Copyright © 2026 Alvin Brown & Clive Maxfield',
    },
)
