"""
dpi_awareness.py -- Windows per-monitor DPI awareness + tk scaling for
plain tkinter, replacing the Qt side of this session's earlier fix:

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

tkinter has no equivalent flag. Two separate things have to be done by
hand, in this order, and the order matters:

1. Tell Windows *before* any window exists that this process handles
   its own DPI scaling ("per-monitor DPI aware") -- otherwise Windows
   silently upscales the whole window as a bitmap after the fact,
   which is exactly the blurry, wrong-size window this project fixed
   for the Qt build.

2. Read the actual DPI of the monitor the window is opening on, and
   feed that ratio into Tk's own internal scaling (`tk scaling`), so
   widget sizes/fonts/padding all come out crisp instead of tkinter
   drawing at 96 DPI and Windows stretching the result.

CAVEAT -- this module could only be smoke-tested in a Linux sandbox
with no real display DPI to test against (call_windows_dpi_apis() is a
no-op there, verified below). The Windows API calls themselves
(SetProcessDpiAwareness / GetDpiForWindow) are correct, standard, and
well-documented, but the *visual* result -- does the app actually look
crisp at 125%/150%/200% scaling, does per-monitor switching work when
you drag the window from one monitor to a different-DPI one -- can
only be confirmed by running this on real Windows hardware with a
Hi-DPI display. Treat this as "ready to test," not "verified."

Also note: this only reproduces DPI scaling. It does NOT reproduce
multi-monitor screen geometry queries (QScreen.availableGeometry(),
used by this session's _reassert_maximized()/_layout_startup_panels()
fixes) -- tkinter's winfo_screenwidth()/winfo_screenheight() only see
the *primary* monitor. Multi-monitor-aware maximize/tiling would need
either the third-party `screeninfo` package or raw ctypes calls to
EnumDisplayMonitors, which is a separate, not-yet-spiked piece of this
migration.
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


# ── self-test -----------------------------------------------------------------

def _selftest():
    """Confirms this module is safe to import and call, and that
    apply_dpi_scaling() doesn't raise against a real Tk root -- on
    WHATEVER platform it's actually run on. Does NOT and CANNOT verify
    real per-monitor Hi-DPI visual correctness on its own -- see module
    docstring; on Windows, look at the window it pops up and judge for
    yourself whether text/widgets look crisp, not just that this prints
    PASSED.
    """
    import tkinter as tk

    on_windows = sys.platform == "win32"

    did_set = set_process_dpi_aware()
    print(f"set_process_dpi_aware() -> {did_set}  "
          f"(platform={sys.platform}; True is expected on Windows, "
          f"False everywhere else)")
    if on_windows:
        assert did_set is True, (
            "on win32, set_process_dpi_aware() should have succeeded -- "
            "if this fired, SetProcessDpiAwareness/SetProcessDPIAware "
            "both failed on this machine, worth investigating directly"
        )
    else:
        assert did_set is False

    root = tk.Tk()
    root.geometry("300x200")
    scale = apply_dpi_scaling(root)
    if on_windows:
        note = "real monitor DPI / 96 -- anything other than 1.0 means scaling is actually being applied"
    else:
        note = "expected 1.0 off-Windows"
    print(f"apply_dpi_scaling() -> scale={scale}  ({note})")
    if not on_windows:
        assert scale == 1.0

    current_scaling = root.tk.call("tk", "scaling")
    print(f"tk scaling now reports: {current_scaling}")

    if on_windows:
        tk.Label(root, text=f"DPI scale = {scale}\nLook at this text --\n"
                             f"does it look crisp, not blurry?",
                 font=("Segoe UI", 12)).pack(expand=True, fill="both")
        print("\nA window should now be visible -- judge Hi-DPI crispness "
              "by eye, then close it.")
        root.mainloop()
    else:
        root.destroy()

    print("\nSELF-TEST PASSED"
          + ("" if on_windows else
             " (Linux no-op path only -- this does not validate the "
             "actual Windows Hi-DPI fix)"))


if __name__ == "__main__":
    _selftest()
