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

# Version is the single source of truth in bin/beboputer_v7/__init__.py
# (__version__) — nothing to edit here, this always tracks the app.
# __init__.py only defines __version__ (no heavy imports), so this is
# a cheap, safe import to do at spec-parse time.
sys.path.insert(0, os.path.join(_root, 'bin'))
from beboputer_v7 import __version__ as _app_version

# The original Data Book PDF is superseded by help/databook/ (an HTML
# conversion) and is no longer shipped in any packaged build. It may still
# be sitting in Data/ on disk (left there rather than deleted), so it's
# filtered out here rather than relying on the source tree being clean.
_EXCLUDE_DATA_FILES = {'The Official DIY Calculator Data Book.pdf'}

# help/databook/ was regenerated as flat page images (page-NNN.png); the
# old databookNNN.png files (previous pdftohtml conversion attempt) may
# still be sitting alongside them on disk, so exclude that glob too.
import fnmatch
_EXCLUDE_PATTERNS = ('databook[0-9][0-9][0-9].png',)


def _dir_datas(src_dir, dest_dir, exclude_basenames=(), exclude_patterns=()):
    """Like a single (src_dir, dest_dir) PyInstaller datas tuple, but
    skips any file whose basename is in exclude_basenames or matches one
    of exclude_patterns (fnmatch-style)."""
    out = []
    for dirpath, _dirnames, filenames in os.walk(src_dir):
        rel = os.path.relpath(dirpath, src_dir)
        for fn in filenames:
            if fn in exclude_basenames:
                continue
            if any(fnmatch.fnmatch(fn, pat) for pat in exclude_patterns):
                continue
            src = os.path.join(dirpath, fn)
            dest = dest_dir if rel == '.' else os.path.join(dest_dir, rel)
            out.append((src, dest))
    return out


a = Analysis(
    [os.path.join(_root, 'bin', 'run_beboputer_v7.py')],

    pathex=[os.path.join(_root, 'bin')],

    binaries=[],

    datas=[
        (os.path.join(_root, 'BITMAPS'),                       'BITMAPS'),
        (os.path.join(_root, 'Config'),                        'Config'),
        *_dir_datas(os.path.join(_root, 'Data'), 'Data', _EXCLUDE_DATA_FILES),
        (os.path.join(_root, 'WorkInProgress'),                'WorkInProgress'),
        (os.path.join(_root, 'tutorial'),                      'tutorial'),
        *_dir_datas(os.path.join(_root, 'help'), 'help', exclude_patterns=_EXCLUDE_PATTERNS),
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
        'CFBundleShortVersionString': _app_version,
        'CFBundleVersion':            _app_version,
        'NSHighResolutionCapable':    True,
        'NSHumanReadableCopyright':   'Copyright © 2026 Alvin Brown & Clive Maxfield',
    },
)
