#!/usr/bin/env python3
"""
make_portable.py -- build a portable (no-install) zip of the tkinter build.

    python make_portable.py

Output:  dist/PY-DIYCALCULATOR-<version>-portable.zip

The zip holds one top-level folder that runs straight from wherever it is
unzipped (USB stick, Desktop, ~/apps ...) on Windows, Raspberry Pi/Linux
and macOS. Needs only a stock Python 3 with tkinter -- no pip installs,
no PyQt5, no admin rights.

Layout mirrors the .deb (RPI_INSTALL/build_deb.sh) so paths.py's
"project root = two levels above beboputer_v7/" rule holds unchanged:

    PY-DIYCALCULATOR-<ver>/
        Beboputer.bat            Windows launcher (no console window)
        Beboputer-console.bat    Windows launcher (shows tracebacks)
        Beboputer.sh             Linux / Raspberry Pi launcher
        Beboputer.command        macOS launcher (double-click in Finder)
        README-PORTABLE.txt
        bin/  BITMAPS/  Config/  Data/  WorkInProgress/  tutorial/  help/
"""

import fnmatch
import os
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "bin"))
from beboputer_v7 import __version__ as VERSION  # noqa: E402

TOP = f"PY-DIYCALCULATOR-{VERSION}"
OUT = ROOT / "dist" / f"{TOP}-portable.zip"

# Whole data folders, same set the .deb / PyInstaller spec ship.
DATA_DIRS = ["BITMAPS", "Config", "Data", "WorkInProgress", "tutorial", "help"]

# Only the runtime parts of bin/ (skip Qt-only launchers, old test
# programs, Arduino sketch, packaging scripts, etc.).
BIN_ITEMS = [
    "beboputer_tk",
    "beboputer_v7",
    "compiler_core.py",
    "das.py",
    "run_beboputer_tk.py",
    "splash.png",
    "splash_about.png",
]

EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", "RPI_INSTALL", "MAC_INSTALL",
                "gui_screenshots"}
EXCLUDE_FILES = {"The Official DIY Calculator Data Book.pdf",  # superseded by help/databook
                 "bin.lnk", "Thumbs.db", ".DS_Store", "desktop.ini"}
EXCLUDE_PATTERNS = ("*.pyc", "*.pyo", "*.spec", "*.iss", "build_*.bat",
                    "build_*.sh", "databook[0-9][0-9][0-9].png")

# ── launchers ────────────────────────────────────────────────────────────

BAT = r"""@echo off
rem PY-DIYCALCULATOR portable launcher (Windows, no console window)
cd /d "%~dp0bin"
where pyw >nul 2>nul && ( start "" pyw -3 run_beboputer_tk.py & exit /b 0 )
where pythonw >nul 2>nul && ( start "" pythonw run_beboputer_tk.py & exit /b 0 )
echo.
echo  Python 3 was not found on this PC.
echo  Install it from https://www.python.org/downloads/  (tick "Add python.exe to PATH"
echo  and keep the default "tcl/tk and IDLE" option), then run this file again.
echo.
pause
"""

BAT_CONSOLE = r"""@echo off
rem PY-DIYCALCULATOR portable launcher (Windows, keeps a console for error output)
cd /d "%~dp0bin"
where py >nul 2>nul && ( py -3 run_beboputer_tk.py & goto done )
where python >nul 2>nul && ( python run_beboputer_tk.py & goto done )
echo  Python 3 was not found on this PC - see README-PORTABLE.txt
:done
pause
"""

SH = """#!/bin/sh
# PY-DIYCALCULATOR portable launcher (Linux / Raspberry Pi / macOS)
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE/bin" || exit 1
PY=$(command -v python3 || command -v python)
if [ -z "$PY" ]; then
    echo "Python 3 not found. Raspberry Pi / Debian: sudo apt install python3 python3-tk"
    exit 1
fi
if ! "$PY" -c "import tkinter" 2>/dev/null; then
    echo "Python found ($PY) but tkinter is missing."
    echo "  Raspberry Pi / Debian / Ubuntu : sudo apt install python3-tk"
    echo "  Fedora                         : sudo dnf install python3-tkinter"
    echo "  macOS                          : use the python.org installer (Homebrew: brew install python-tk)"
    exit 1
fi
exec "$PY" run_beboputer_tk.py "$@"
"""

COMMAND = """#!/bin/sh
# macOS: double-click in Finder. First time: right-click > Open if Gatekeeper complains.
exec "$(dirname "$0")/Beboputer.sh" "$@"
"""

README = f"""PY-DIYCALCULATOR {VERSION} -- portable edition
=============================================

No installer. Unzip anywhere (Desktop, USB stick, ~/apps ...) and run.

Requirements
------------
  Python 3.10 or newer with tkinter. Nothing else -- no pip packages.

  Windows       python.org installer (tkinter is included by default).
  Raspberry Pi  sudo apt install python3 python3-tk
  macOS         python.org installer (Homebrew users: brew install python-tk)

Starting the app
----------------
  Windows       double-click  Beboputer.bat
                (Beboputer-console.bat does the same but keeps a window
                 open showing any error messages)
  Pi / Linux    ./Beboputer.sh        (or: sh Beboputer.sh)
  macOS         double-click  Beboputer.command
                (first time: right-click > Open)

  If the .sh / .command file lost its execute bit while unzipping:
      chmod +x Beboputer.sh Beboputer.command

Where things live
-----------------
  Data/            sample .asm programs (default Open folder)
  tutorial/        tutorial exercises
  WorkInProgress/  default Save folder -- your work stays with the app
  help/            HTML help + Data Book (Help menu)

  Note: custom calculator button definitions are saved per user
  (Windows: %APPDATA%\\PY-DIYCALCULATOR, elsewhere: your home folder),
  not inside this folder.

Uninstall
---------
  Delete the folder.

Copyright (c) 2026 Alvin Brown & Clive Maxfield -- MIT licence.
"""


def _skip(name: str, is_dir: bool) -> bool:
    if is_dir:
        return name in EXCLUDE_DIRS
    return name in EXCLUDE_FILES or any(fnmatch.fnmatch(name, p) for p in EXCLUDE_PATTERNS)


def _walk(src: Path):
    if src.is_file():
        if not _skip(src.name, False):
            yield src
        return
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = sorted(d for d in dirnames if not _skip(d, True))
        for fn in sorted(filenames):
            if not _skip(fn, False):
                yield Path(dirpath) / fn


def _add_text(zf: zipfile.ZipFile, arcname: str, text: str, executable=False, crlf=False):
    data = text.replace("\n", "\r\n") if crlf else text
    info = zipfile.ZipInfo(arcname, date_time=time.localtime()[:6])
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3  # unix, so the mode bits below are honoured
    info.external_attr = ((0o100755 if executable else 0o100644) & 0xFFFF) << 16
    zf.writestr(info, data.encode("utf-8"))


def main() -> None:
    sources = [ROOT / d for d in DATA_DIRS] + [ROOT / "bin" / b for b in BIN_ITEMS]
    missing = [str(p.relative_to(ROOT)) for p in sources if not p.exists()]
    if missing:
        sys.exit(f"ERROR: missing from project: {', '.join(missing)}")

    OUT.parent.mkdir(exist_ok=True)
    count = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src in sources:
            for f in _walk(src):
                zf.write(f, f"{TOP}/{f.relative_to(ROOT).as_posix()}")
                count += 1
        _add_text(zf, f"{TOP}/Beboputer.bat", BAT, crlf=True)
        _add_text(zf, f"{TOP}/Beboputer-console.bat", BAT_CONSOLE, crlf=True)
        _add_text(zf, f"{TOP}/Beboputer.sh", SH, executable=True)
        _add_text(zf, f"{TOP}/Beboputer.command", COMMAND, executable=True)
        _add_text(zf, f"{TOP}/README-PORTABLE.txt", README, crlf=True)
        count += 5

    print(f"{OUT}  ({count} files, {OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
