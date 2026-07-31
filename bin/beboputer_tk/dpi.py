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
dpi.py -- Windows per-monitor DPI awareness + tk scaling for plain
tkinter, replacing the Qt side of beboputer_v7/app.py's:

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

tkinter has no equivalent flag, so this does it by hand, in order:

1. set_process_dpi_aware() -- tell Windows *before* any window exists
   that this process handles its own DPI scaling, so Windows doesn't
   silently upscale the whole window as a blurry bitmap after the
   fact. Call this first, before Tk().
2. apply_dpi_scaling(root) -- once the root window exists, read the
   real monitor DPI and feed the ratio into Tk's own internal scaling
   so widget/font sizes render crisp instead of tkinter drawing at 96
   DPI and Windows stretching the result.

Verified crisp/readable on real Windows hardware during this
migration's Phase 0 spike (see prototypes/tkinter_migration/
dpi_awareness.py and TKINTER_MIGRATION.md, sec. 3.3, for the full
spike writeup and self-test). Still worth a spot-check at other
scaling levels (125%/150%/200%) and across a multi-monitor drag if
that hardware is available.

Does NOT reproduce multi-monitor screen geometry queries
(QScreen.availableGeometry(), used by beboputer_v7's
_reassert_maximized()/_layout_startup_panels()) -- winfo_screenwidth()/
winfo_screenheight() only see the primary monitor. That's a separate,
not-yet-built piece of this migration (see TKINTER_MIGRATION.md).
"""

from __future__ import annotations

import sys
import ctypes


PROCESS_PER_MONITOR_DPI_AWARE = 2  # MDT_EFFECTIVE_DPI equivalent
BASE_DPI = 96.0


def set_process_dpi_aware() -> bool:
    """Call this ONCE, before creating the Tk() root. Returns True if
    it actually did something (i.e. running on Windows), False on any
    other platform or if the call failed (older Windows without
    shcore.dll -- falls back to the coarser SetProcessDPIAware)."""
    if sys.platform != "win32":
        return False
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
        return True
    except (AttributeError, OSError):
        pass
    try:
        # Windows Vista/7/8 without per-monitor support -- system-DPI-aware
        # is still much better than not being DPI-aware at all.
        ctypes.windll.user32.SetProcessDPIAware()
        return True
    except (AttributeError, OSError):
        return False


def get_window_dpi(root) -> int:
    """Query the DPI of the monitor *root* (a Tk widget, typically the
    root window, already created and mapped) currently sits on.
    Returns 96 (no scaling) on any non-Windows platform or on error --
    the safe default that leaves tk's own scaling untouched."""
    if sys.platform != "win32":
        return int(BASE_DPI)
    try:
        hwnd = root.winfo_id()
        # GetDpiForWindow needs Windows 10 1607+; wrapped so an older
        # Windows just falls back to the 96-DPI default rather than
        # crashing the app.
        return ctypes.windll.user32.GetDpiForWindow(hwnd)
    except (AttributeError, OSError):
        return int(BASE_DPI)


def apply_dpi_scaling(root) -> float:
    """Read the real monitor DPI and set Tk's internal scaling to
    match, so widget/font sizes render crisp instead of blurry-
    stretched. Call this once, right after the root window is created
    (needs a real hwnd, so after root.update_idletasks() at the
    earliest). Returns the scale factor applied, e.g. 1.25 at 125%.
    """
    root.update_idletasks()
    dpi = get_window_dpi(root)
    scale = dpi / BASE_DPI
    # tk's own scaling is expressed in points-per-pixel; the standard
    # conversion recommended by the Tk docs for matching OS DPI scaling.
    root.tk.call("tk", "scaling", scale)
    return scale
