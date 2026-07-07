# Copyright (c) 2026 Alvin Brown & Clive Maxfield
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
paths.py — portable data-file resolver.

Works in two modes:

1. **Source / development**
   ``resource_path('BITMAPS', 'USEG0.BMP')`` resolves relative to the
   project root (the folder that *contains* ``bin/``).  This is two
   directory levels above this file::

       <project_root>/
           BITMAPS/
           Config/
           bin/
               beboputer_v7/
                   paths.py   ← this file

2. **PyInstaller bundle** (``sys.frozen == True``)
   All data files are extracted to ``sys._MEIPASS`` by the bundler.
   ``resource_path`` simply joins the requested parts onto that temp root.

Usage
-----
    from .paths import resource_path

    bmp  = resource_path('BITMAPS', 'USEG0.BMP')
    ini  = resource_path('Config', 'DIYCALC.INI')
    html = resource_path('beboputer_v7_help.html')
"""

import os
import shutil
import sys
from pathlib import Path


def resource_path(*parts: str) -> str:
    """Return the absolute path to a bundled data file or folder.

    Parameters
    ----------
    *parts:
        Path components relative to the project / bundle root,
        e.g. ``resource_path('BITMAPS', 'USEG0.BMP')``.
    """
    if getattr(sys, 'frozen', False):
        # Running inside a PyInstaller bundle — data lives in _MEIPASS.
        base = sys._MEIPASS                          # type: ignore[attr-defined]
    else:
        # Running from source — project root is two levels above this file:
        # paths.py → beboputer_v7/ → bin/ → <project_root>/
        base = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
        )
    return os.path.normpath(os.path.join(base, *parts))


# ── Open/Save dialog defaults ────────────────────────────────────────────────
#
# In a packaged build the app's own folder is not reliably writable by a
# non-admin user:
#   Windows  →  C:\Program Files\...\_internal\  (admin-only write)
#   Pi .deb  →  /usr/share/beboputer/             (root-owned)
#   macOS    →  inside the read-only .app bundle
#
# So for frozen builds we keep one ordinary, writable folder in the user's
# own space — seeded on first run with copies of the bundled sample .asm
# files — and default *both* the Open and Save dialogs to it.  A user's own
# work and the sample programs then live side by side in one place that
# has nothing to do with where the app happens to be installed.
#
# Running from source keeps the old split (Data/ for samples,
# WorkInProgress/ for saves) since both already sit right next to the code
# and are writable during development.

_WORKSPACE_NAME = "PY-DIYCALCULATOR"


def user_workspace_dir() -> Path:
    """Writable folder used as the Open/Save default in packaged builds.

    Created under ~/Documents (falling back to the home folder itself if
    there's no Documents folder) and seeded with copies of the bundled
    sample files on every run.

    Seed sources:
      Data/      — the official sample .asm programs. Existing files are
                   never overwritten here, so a user's own edits/renames/
                   saves under that name are safe on every run.
      tutorial/  — the tutorial's .asm walkthrough programs (the
                   accompanying *_Tutorial.docx files are left where they
                   are; only assembly source is copied in here). These
                   ARE overwritten every run so a bug fix to a tutorial
                   program (shipped in a new install/update) actually
                   reaches a machine that already has an older copy
                   sitting in the workspace from a previous run — a
                   real, reported problem: a fixed
                   10_calculator_four_function.asm kept getting shadowed
                   by the stale pre-fix copy already seeded here, so the
                   old bug (e.g. 4/2 showing 1 instead of 2) persisted
                   after the app itself was updated. Tutorials are
                   reference material meant to match the docs exactly;
                   anyone wanting to experiment should Save As under a
                   different name rather than edit these in place.
    """
    docs = Path.home() / "Documents"
    base = docs if docs.is_dir() else Path.home()
    workspace = base / _WORKSPACE_NAME
    workspace.mkdir(parents=True, exist_ok=True)

    try:
        for seed_name, only_asm, always_refresh in (
            ('Data', False, False),
            ('tutorial', True, True),
        ):
            bundled = Path(resource_path(seed_name))
            if not bundled.is_dir():
                continue
            for f in bundled.iterdir():
                if not f.is_file():
                    continue
                if only_asm and f.suffix.lower() != '.asm':
                    continue
                dest = workspace / f.name
                if always_refresh or not dest.exists():
                    shutil.copy2(f, dest)
    except Exception:
        pass   # Never let sample-seeding stop the app from starting.

    return workspace


def default_open_dir() -> str:
    """Best initial directory for Open dialogs."""
    if getattr(sys, 'frozen', False):
        return str(user_workspace_dir())
    data_dir = Path(resource_path('Data'))
    if data_dir.is_dir():
        return str(data_dir)
    return str(Path.home())


def default_save_dir() -> str:
    """Best writable initial directory for Save dialogs."""
    if getattr(sys, 'frozen', False):
        return str(user_workspace_dir())
    wip_dir = Path(resource_path('WorkInProgress'))
    if wip_dir.is_dir() and os.access(str(wip_dir), os.W_OK):
        return str(wip_dir)
    user_dir = Path.home() / 'beboputer'
    user_dir.mkdir(exist_ok=True)
    return str(user_dir)
