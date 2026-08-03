# -*- mode: python ; coding: utf-8 -*-

import os

# The original Data Book PDF is superseded by help/databook/ (an HTML
# conversion) and is no longer shipped in any packaged build. It may still
# be sitting in Data/ on disk (left there rather than deleted), so it's
# filtered out here rather than relying on the source tree being clean.
_EXCLUDE_DATA_FILES = {'The Official DIY Calculator Data Book.pdf'}


def _dir_datas(src_dir, dest_dir, exclude_basenames=()):
    """Like a single (src_dir, dest_dir) PyInstaller datas tuple, but
    skips any file whose basename is in exclude_basenames."""
    out = []
    for dirpath, _dirnames, filenames in os.walk(src_dir):
        rel = os.path.relpath(dirpath, src_dir)
        for fn in filenames:
            if fn in exclude_basenames:
                continue
            src = os.path.join(dirpath, fn)
            dest = dest_dir if rel == '.' else os.path.join(dest_dir, rel)
            out.append((src, dest))
    return out


a = Analysis(
    ['bin\\run_beboputer_v7.py'],
    pathex=['bin'],
    binaries=[],
    datas=[
        ('BITMAPS', 'BITMAPS'),
        ('Config', 'Config'),
        *_dir_datas('Data', 'Data', _EXCLUDE_DATA_FILES),
        ('WorkInProgress', 'WorkInProgress'),
        ('tutorial', 'tutorial'),
        ('help', 'help'),
    ],
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
    [],
    exclude_binaries=True,
    name='Beboputer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name='Beboputer',
)
