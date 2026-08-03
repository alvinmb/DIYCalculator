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
test_gui_smoke.py -- visual regression smoke test for the tkinter build.

Drives every beboputer_tk menu command that opens a panel or dialog
("form"), and checks that it actually renders: the window exists, is
mapped, and has a real (non-zero) size. This is the kind of regression
this suite didn't have before -- test_cpu.py/test_compiler_core.py/
test_asm_regression.py exercise the CPU/assembler directly and never touch
a single widget, so a change that leaves a panel blank, zero-sized, or
raising an exception on open (e.g. the Calculator scrollbar-clutter fix,
or the Pi window-maximize fix earlier in this project's history) would
sail through every other test in this repo untouched.

Screenshots (best-effort only -- see _snapshot()) are written to
tests/gui_screenshots/<name>.png for manual visual review; they are
NOT compared against a baseline or asserted on, since pixel-diffing
across fonts/DPI/platforms is exactly the kind of flakiness
TKINTER_MIGRATION.md already calls out as out of scope. Treat that
folder as a "here's what it actually looked like" artifact, not a
pass/fail signal.

Requires a real or virtual (Xvfb) X display -- tkinter cannot run truly
headless. The whole module is skipped automatically if a Tk window can't
be created (e.g. no DISPLAY env var and no Xvfb running):

    xvfb-run -a pytest tests/test_gui_smoke.py -v

Deliberately NOT exercised here -- not "forms" to visually check, or
have side effects an automated smoke test shouldn't trigger:
  File menu   -- New/Open/Save Project, Load/Save RAM, Purge RAM (file
                 dialogs block waiting for real user input; New/Purge
                 destroy RAM state), Exit (closes the app).
  Setup menu  -- Load/Save Button File (file dialog), Restore Defaults
                 (destructive to the calculator's button config),
                 System Clock (its own dialog IS covered, see
                 test_system_clock_dialog_opens_and_renders), Interrupt
                 (a CPU action, not a form).
  Help menu   -- Help... and "DIY Calculator on the web" open an
                 external browser -- a side effect outside the app,
                 not an in-app form.
"""

from __future__ import annotations

import os
import sys
import time

import pytest

# Point Tcl at its own library explicitly, before tkinter ever creates a
# Tk() instance, instead of trusting its runtime auto-detection.
#
# On at least one Windows/Python 3.14 install (the newer per-user
# "Python Install Manager" layout under
# %LocalAppData%\Python\pythoncore-<ver>-64\), running `python -m
# beboputer_tk` directly finds tcl8.6/init.tcl fine every time, but
# running the exact same interpreter via `python -m pytest` reliably
# fails with "Can't find a usable init.tcl" / "invalid command name
# tcl_findLibrary" -- every single tk.Tk() call, every run. This only
# sets the env vars if they aren't already set AND the guessed path
# actually exists, so it's a no-op anywhere this isn't needed
# (Linux/macOS, or a Windows install that isn't affected).
if sys.platform == "win32" and "TCL_LIBRARY" not in os.environ:
    # Directory name is just "tcl8.6"/"tk8.6" regardless of the Python
    # version -- Tcl 8.6 has been CPython's bundled version for years.
    _tcl_dir = os.path.join(sys.base_prefix, "tcl")
    _tcl_lib = os.path.join(_tcl_dir, "tcl8.6")
    _tk_lib = os.path.join(_tcl_dir, "tk8.6")
    if os.path.isfile(os.path.join(_tcl_lib, "init.tcl")):
        os.environ["TCL_LIBRARY"] = _tcl_lib
    if os.path.isdir(_tk_lib):
        os.environ["TK_LIBRARY"] = _tk_lib

tk = pytest.importorskip("tkinter")
from tkinter import messagebox  # noqa: E402

# conftest.py already does this for every test module, but keep this file
# runnable standalone too (e.g. `python -m pytest tests/test_gui_smoke.py`
# from a different cwd).
_BIN = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "bin"))
if _BIN not in sys.path:
    sys.path.insert(0, _BIN)


def _new_tk_root(attempts: int = 3, delay: float = 0.3) -> "tk.Tk":
    """tk.Tk(), retrying a few times on TclError.

    The Windows/pytest init.tcl failure above (see the TCL_LIBRARY block)
    was reported to hit 100% of attempts in one run and 0% running the
    same code directly -- but the *file* Tcl fails to read demonstrably
    exists (Tcl's own error message names the correct directory), so this
    isn't a wrong-path problem TCL_LIBRARY alone is guaranteed to fix; it
    has the shape of a transient read failure (something else briefly
    holding the file -- antivirus real-time scanning is the usual
    culprit for exactly this symptom on Windows). A short retry loop
    costs nothing when everything's fine and rides out a one-off lock
    when it isn't.
    """
    last_exc = None
    for attempt in range(attempts):
        try:
            return tk.Tk()
        except tk.TclError as exc:
            last_exc = exc
            if attempt < attempts - 1:
                time.sleep(delay)
    raise last_exc


# -- skip the whole module if there's no display to open a real Tk window --
try:
    _probe = _new_tk_root()
    _probe.withdraw()
    _probe.destroy()
except tk.TclError as _exc:  # pragma: no cover -- environment-dependent
    pytest.skip(
        f"no display available for tkinter ({_exc}) -- "
        f"run under Xvfb, e.g. `xvfb-run -a pytest {__file__}`",
        allow_module_level=True,
    )

from beboputer_tk.main_window import BebopMain  # noqa: E402
from beboputer_tk.dialogs.eprom_burner import EpromBurner  # noqa: E402
from beboputer_tk.dialogs.about import AboutDialog  # noqa: E402

try:
    from PIL import ImageGrab
    _HAVE_IMAGEGRAB = True
except ImportError:  # pragma: no cover
    _HAVE_IMAGEGRAB = False

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "gui_screenshots")

# menu_key (BebopMain._panels / PANEL_TITLES key) -> (show-method name, label)
# every one of these is opened via BebopMain._open_panel() and tracked in
# self._panels, so they can all be checked the same generic way.
MDI_PANEL_COMMANDS = [
    ("calculator",   "_show_calculator",   "Calculator"),
    ("mem_walker",   "_show_mem_walker",   "Memory Walker"),
    ("msg_display",  "_show_msg_display",  "Message Display"),
    ("cpu",          "_show_cpu",          "CPU Registers"),
    ("terminal",     "_show_terminal",     "Terminal"),
    ("ports",        "_show_ports",        "Port Map Status"),
    ("disassembler", "_show_disassembler", "Disassembler"),
    ("keyboard",     "_show_keyboard",     "Keyboard"),
    ("workbench",    "_show_workbench",    "Workbench 1"),
    ("compiler",     "_show_compiler",     "Assembler / Editor"),
]

EXPECTED_TOP_MENUS = ["File", "Setup", "Display", "Memory", "Tools", "Help"]


@pytest.fixture(scope="session")
def _root():
    """One tk.Tk() root, reused for the whole test session rather than a
    fresh interpreter per test -- both to minimize Tcl interpreter churn
    in general, and because creating it is the exact call that can hit
    the Windows/pytest init.tcl issue described above _new_tk_root();
    doing it once per session (with retries) rather than once per test
    keeps that risk to a single attempt instead of sixteen. Reusing one
    root and just tearing down its widget tree between tests (see the
    app fixture below) is what makes that possible without any one test
    leaking state into the next."""
    root = _new_tk_root()
    yield root
    root.destroy()


@pytest.fixture
def app(_root):
    """A fresh BebopMain per test, built in the shared session root
    (see _root) with the previous test's widget tree cleared first."""
    for child in _root.winfo_children():
        child.destroy()
    _root.geometry("1200x800+0+0")
    _root.update()
    main = BebopMain(_root)
    _root.update()
    yield main
    for child in _root.winfo_children():
        child.destroy()


@pytest.fixture(autouse=True)
def _no_blocking_dialogs(monkeypatch):
    """Auto-answer any messagebox popup instead of letting it block the
    test waiting for a real click -- Credits (_show_credits) uses
    messagebox.showinfo(), and any code path that unexpectedly pops an
    error/warning box would otherwise hang the whole test run rather
    than failing it."""
    calls = []

    def _record(name):
        def _fn(title, message, *a, **kw):
            calls.append((name, title, message))
            return True
        return _fn

    monkeypatch.setattr(messagebox, "showinfo", _record("showinfo"))
    monkeypatch.setattr(messagebox, "showerror", _record("showerror"))
    monkeypatch.setattr(messagebox, "showwarning", _record("showwarning"))
    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **kw: True)
    return calls


def _snapshot(widget, name):
    """Best-effort screenshot -- never fails the test. Silently skipped
    if Pillow's ImageGrab isn't available or the display can't be
    captured (e.g. some virtual framebuffers)."""
    if not _HAVE_IMAGEGRAB:
        return
    widget.update_idletasks()
    x, y = widget.winfo_rootx(), widget.winfo_rooty()
    w, h = widget.winfo_width(), widget.winfo_height()
    if w <= 1 or h <= 1:
        return
    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        img.save(os.path.join(SCREENSHOT_DIR, f"{name}.png"))
    except Exception:
        pass


def _assert_renders(widget, label):
    widget.update_idletasks()
    assert widget.winfo_exists(), f"{label}: window doesn't exist"
    assert widget.winfo_ismapped(), f"{label}: window isn't mapped/visible"
    assert widget.winfo_width() > 1 and widget.winfo_height() > 1, (
        f"{label}: rendered with a zero/near-zero size "
        f"({widget.winfo_width()}x{widget.winfo_height()})"
    )


# ------------------------------------------------------------- menu bar --

def test_menu_bar_has_all_top_level_menus(app):
    """Sanity check the bar itself built successfully with every expected
    top-level menu -- catches e.g. an exception partway through
    _build_menu() silently dropping the rest of the bar."""
    labels = [
        child["text"] for child in app._menubar_frame.winfo_children()
        if isinstance(child, tk.Menubutton)
    ]
    assert labels == EXPECTED_TOP_MENUS


# --------------------------------------------------------- MDI panels --

@pytest.mark.parametrize("panel_key,method_name,label", MDI_PANEL_COMMANDS)
def test_panel_opens_and_renders(app, panel_key, method_name, label):
    show = getattr(app, method_name)
    show()
    app.root.update()
    child = app._panels.get(panel_key)
    assert child is not None, f"{label}: command did not open a tracked panel"
    _assert_renders(child, label)
    _snapshot(child, f"panel_{panel_key}")
    child.close()


def test_all_panels_open_together(app):
    """Open every panel at once (closer to real usage than one-at-a-time)
    and snapshot the whole app window as a single combined reference."""
    for _key, method_name, _label in MDI_PANEL_COMMANDS:
        getattr(app, method_name)()
    app.root.update()
    for panel_key, _method_name, label in MDI_PANEL_COMMANDS:
        child = app._panels.get(panel_key)
        assert child is not None, f"{label}: not open in the combined pass"
        _assert_renders(child, f"{label} (combined)")
    _snapshot(app.root, "all_panels_combined")


# ----------------------------------------------------- Toplevel dialogs --

def test_eprom_burner_opens_and_renders(app):
    app._show_eprom()
    app.root.update()
    dialogs = [w for w in app.root.winfo_children() if isinstance(w, EpromBurner)]
    assert dialogs, "EPROM Burner: no dialog window appeared"
    dlg = dialogs[-1]
    _assert_renders(dlg, "EPROM Burner")
    _snapshot(dlg, "dialog_eprom_burner")
    dlg.destroy()


def test_about_dialog_opens_and_renders(app):
    app._show_about()
    app.root.update()
    dialogs = [w for w in app.root.winfo_children() if isinstance(w, AboutDialog)]
    assert dialogs, "About: no dialog window appeared"
    dlg = dialogs[-1]
    _assert_renders(dlg, "About")
    _snapshot(dlg, "dialog_about")
    dlg.destroy()


def test_system_clock_dialog_opens_and_renders(app):
    # ask_hz() (dialogs/system_clock.py) builds its own tk.Toplevel and
    # blocks on it internally (wait_window) -- schedule the "Cancel"-
    # equivalent dismissal via after() so this doesn't hang, same
    # approach as _no_blocking_dialogs uses for messagebox.
    def _dismiss():
        for w in app.root.winfo_children():
            if isinstance(w, tk.Toplevel) and w.title() == "System Clock":
                _assert_renders(w, "System Clock")
                _snapshot(w, "dialog_system_clock")
                w.destroy()
                return
    app.root.after(200, _dismiss)
    app._set_clock()
    app.root.update()


# ------------------------------------------------------- mocked dialogs --

def test_credits_shows_expected_message(app, _no_blocking_dialogs):
    app._show_credits()
    calls = _no_blocking_dialogs
    assert any(name == "showinfo" for name, _title, _msg in calls), (
        "Credits: expected a messagebox.showinfo() call"
    )
