# -*- mode: python ; coding: utf-8 -*-
#
# beboputer_tk.spec — PyInstaller build recipe for the tkinter port
# ───────────────────────────────────────────────────────────────
# Mirrors bin/beboputer_v7/beboputer.spec (the original PyQt5 build)
# exactly in structure, pointed at the tkinter entry point instead.
# tkinter itself ships with every standard CPython install, so unlike
# the Qt build there's no PyQt5 wheel/hiddenimports to worry about --
# the only third-party runtime dependency this app has (Pillow, for
# workbench.py's BITMAPS conversion) is a *dev-time-only* tool; the
# pre-converted PNGs it produced are plain data files, loaded at
# runtime via tk.PhotoImage, so no Pillow import ever happens here.
#
# Run from the project root (Bebop_python/) with:
#
#   pyinstaller bin/beboputer_tk/beboputer_tk.spec
#
# Output lands in  dist/Beboputer/
#
# Requirements (install once per machine):
#   pip install pyinstaller
#   (tkinter itself: already bundled with python.org/Microsoft Store
#   Python on Windows and python.org installers on macOS; on Linux,
#   install the OS package first -- e.g. `sudo apt install python3-tk`
#   -- python-from-source builds sometimes omit it.)
#
# Build on each target platform natively (PyInstaller does not
# cross-compile -- a Windows .exe must be built ON Windows, see
# build_installer.bat in this same folder):
#   Windows  →  dist/Beboputer/Beboputer.exe  (+ support folder)
#   macOS    →  dist/Beboputer.app
#   Linux    →  dist/Beboputer/Beboputer      (+ support folder --
#                though RPI_INSTALL/build_deb.sh is the recommended
#                Linux/Raspberry Pi path instead of this spec, since
#                it ships Python source directly rather than a frozen
#                binary, so it runs on every Pi model/architecture)

block_cipher = None

import os

# SPECPATH is injected by PyInstaller = the folder containing this .spec
# file (bin/beboputer_tk/). Project root is two levels up. Resolving it
# this way means the build works regardless of where the repo is
# checked out.
_root = os.path.normpath(os.path.join(SPECPATH, '..', '..'))

# The original Data Book PDF is superseded by help/databook/ (an HTML
# conversion) and is no longer shipped in any packaged build. It may still
# be sitting in Data/ on disk (left there rather than deleted -- see
# project notes), so it's filtered out here rather than relying on the
# source tree being clean.
_EXCLUDE_DATA_FILES = {'The Official DIY Calculator Data Book.pdf'}

# help/databook/ was regenerated as flat page images (page-NNN.png) after
# the original pdftohtml "complex mode" conversion (databookNNN.png + a
# CSS-font-styled text overlay) turned out to have font-substitution bugs
# -- text drifting into diagrams when the viewing browser lacked a font
# matching the PDF's internal font name. The old databookNNN.png files may
# still be sitting alongside the new ones on disk, so exclude that glob
# pattern too.
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
    # ── entry point ──────────────────────────────────────────────────
    [os.path.join(_root, 'bin', 'run_beboputer_tk.py')],

    # ── import paths — 'bin/' must be on sys.path so the package is found ───
    pathex=[os.path.join(_root, 'bin')],

    binaries=[],

    # ── data files ───────────────────────────────────────────────────
    # Tuples are (source_on_disk, dest_inside_bundle). All destinations
    # are relative to sys._MEIPASS (the bundle root) -- paths.py's
    # resource_path() and the ad-hoc bin/-relative lookups in app.py /
    # about.py / main_window.py both resolve against that same root
    # when sys.frozen is True, so this list must mirror exactly what
    # those modules read from disk at runtime:
    #   BITMAPS/    -- workbench 7-seg PNGs, port/LED art, app icon
    #   Config/     -- DIYCALC.INI, defbuttons.ini
    #   Data/       -- bundled sample .asm programs (the superseded PDF
    #                   Data Book is excluded below -- see _EXCLUDE_DATA_FILES)
    #   WorkInProgress/ -- default Save location when running from source
    #   tutorial/   -- tutorial walkthrough .asm files
    #   help/       -- beboputer_v7_help.html + databook/ (the HTML edition
    #                   of the Data Book). Bundled as a whole folder at the
    #                   same relative depth as the source checkout and the
    #                   .deb install, so the help file's own relative links
    #                   (e.g. to databook/index.html) resolve identically in
    #                   every run context. See main_window._show_help() and
    #                   dialogs/about.py's "Beboputer Databook" button.
    #   bin/splash.png       -- startup splash (app.py)
    #   bin/splash_about.png -- About dialog image, pre-scaled 200x200
    #                            (dialogs/about.py)
    datas=[
        (os.path.join(_root, 'BITMAPS'),                        'BITMAPS'),
        (os.path.join(_root, 'Config'),                         'Config'),
        *_dir_datas(os.path.join(_root, 'Data'), 'Data', _EXCLUDE_DATA_FILES),
        (os.path.join(_root, 'WorkInProgress'),                 'WorkInProgress'),
        (os.path.join(_root, 'tutorial'),                       'tutorial'),
        *_dir_datas(os.path.join(_root, 'help'), 'help', exclude_patterns=_EXCLUDE_PATTERNS),
        (os.path.join(_root, 'bin', 'splash.png'),              '.'),
        (os.path.join(_root, 'bin', 'splash_about.png'),        '.'),
    ],

    hiddenimports=[],

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
    # Reuses the same brand icon as the Qt build's spec -- one level
    # up from this file, in bin/beboputer_v7/.
    icon=os.path.join(SPECPATH, '..', 'beboputer_v7', 'beboputer.ico'),
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

# ── macOS: wrap everything in a .app bundle ───────────────────────────
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
