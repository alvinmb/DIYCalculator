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
main_window.py -- tkinter Phase 1 shell for PY-DIYCALCULATOR.

This is the tkinter counterpart of beboputer_v7/main_window.py's
BebopMain, scoped to Phase 1 of TKINTER_MIGRATION.md: real menu bar,
real status bar, real MdiArea, real non-overlapping startup layout --
but every panel a menu item opens is still a placeholder MdiChild
("coming in Phase 2"), since porting each panel's actual content is
Phase 2's job, not this one's. The point of Phase 1 is a working,
navigable app skeleton to build that content into.

Menu structure (labels, grouping, and order) is copied directly from
beboputer_v7/menus.py so the tkinter build feels like the same app
from the moment you open it, not a stripped-down cousin.

The CPU engine, assembler, defbuttons.ini format, and resource_path()
are all reused unchanged -- see TKINTER_MIGRATION.md sec. 1.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from .mdi import MdiArea, MdiChild, PanelSpec, tile_children

try:
    from beboputer_v7 import __version__
except ImportError:  # pragma: no cover - shouldn't happen once packaged
    __version__ = "0.0.0-dev"

try:
    from beboputer_v7.styles import C
except ImportError:  # pragma: no cover
    C = {"bg": "#c0c0c0", "grey": "#606060"}


PLACEHOLDER_NOTE = (
    "This panel is a Phase 1 placeholder.\n\n"
    "Real content lands in Phase 2 of the tkinter migration --\n"
    "see TKINTER_MIGRATION.md for the sequencing."
)


class BebopMain:
    """tkinter counterpart of beboputer_v7.main_window.BebopMain,
    scoped to Phase 1 (shell only -- see module docstring)."""

    # (menu_key, title) pairs for every panel the Qt app's menus open.
    # menu_key is also used as the MdiChild registry key, so re-opening
    # an already-open panel raises it instead of creating a duplicate --
    # the same behaviour QMdiArea gives the Qt app for free.
    PANEL_TITLES = {
        "calculator":    "Calculator",
        "mem_walker":    "Memory Walker",
        "msg_display":   "Message Display",
        "cpu":           "CPU Registers",
        "terminal":      "Terminal",
        "ports":         "Port Map Status",
        "disassembler":  "Disassembler",
        "eprom":         "EPROM Burner",
        "keyboard":      "Keyboard",
        "workbench":     "Workbench 1",
        "compiler":      "Assembler / Editor",
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        self._panels: dict[str, MdiChild] = {}  # menu_key -> MdiChild

        root.title(f"PY-DIYCALCULATOR  v{__version__}  (tkinter Phase 1)")
        root.configure(bg=C.get("bg", "#c0c0c0"))
        root.geometry("1200x800")
        try:
            root.state("zoomed")  # Windows/most Linux WMs: maximize on launch
        except tk.TclError:
            pass  # some WMs (notably certain macOS Tk builds) don't support "zoomed"

        self._build_menu()
        self._build_statusbar()
        self._build_mdi()
        self._open_startup_panels()

        self.set_status("Ready")

    # ------------------------------------------------------------ menu --

    def _build_menu(self):
        mb = tk.Menu(self.root)
        self.root.config(menu=mb)

        # ── File ─────────────────────────────────────────────────────────
        fm = tk.Menu(mb, tearoff=0)
        mb.add_cascade(label="File", menu=fm)
        fm.add_command(label="New Project...",     command=self._new_project)
        fm.add_command(label="Open Project...",    command=self._open_project)
        fm.add_command(label="Save Project...",    command=self._save_project)
        fm.add_command(label="Save Project As...", command=self._save_project_as)
        fm.add_separator()
        fm.add_command(label="Load RAM...",  command=self._load_ram)
        fm.add_command(label="Save RAM...",  command=self._save_ram)
        fm.add_command(label="Purge RAM...", command=self._purge_ram)
        fm.add_separator()
        fm.add_command(label="Exit", command=self._exit)

        # ── Setup ────────────────────────────────────────────────────────
        sm = tk.Menu(mb, tearoff=0)
        mb.add_cascade(label="Setup", menu=sm)
        sm.add_command(label="System Clock...",   command=self._set_clock)
        sm.add_separator()
        sm.add_command(label="Load Button File...", command=self._load_button_file)
        sm.add_command(label="Save Button File...", command=self._save_button_file)
        sm.add_command(label="Restore Defaults",    command=self._restore_defaults)

        # ── Display ──────────────────────────────────────────────────────
        dm = tk.Menu(mb, tearoff=0)
        mb.add_cascade(label="Display", menu=dm)
        dm.add_command(label="CPU Registers",   command=self._show_cpu)
        dm.add_command(label="Message Display", command=self._show_msg_display)
        dm.add_command(label="Terminal",        command=self._show_terminal)
        dm.add_command(label="Port Map Status", command=self._show_ports)
        dm.add_command(label="Disassembler",    command=self._show_disassembler)

        # ── Memory ───────────────────────────────────────────────────────
        mm = tk.Menu(mb, tearoff=0)
        mb.add_cascade(label="Memory", menu=mm)
        mm.add_command(label="Memory Walker",   command=self._show_mem_walker)
        mm.add_command(label="Find Address...", command=self._find_address)

        # ── Tools ────────────────────────────────────────────────────────
        tm = tk.Menu(mb, tearoff=0)
        mb.add_cascade(label="Tools", menu=tm)
        tm.add_command(label="EPROM Burner",         command=self._show_eprom)
        tm.add_command(label="Calculator...",        command=self._show_calculator)
        tm.add_command(label="Keyboard...",          command=self._show_keyboard)
        tm.add_command(label="Workbench 1...",       command=self._show_workbench)
        tm.add_command(label="Assembler / Editor...", command=self._show_compiler)

        # ── Help ─────────────────────────────────────────────────────────
        hm = tk.Menu(mb, tearoff=0)
        mb.add_cascade(label="Help", menu=hm)
        hm.add_command(label="Help...", command=self._show_help)
        hm.add_command(label="DIY Calculator on the web", command=self._show_web)
        hm.add_separator()
        hm.add_command(label="About...",   command=self._show_about)
        hm.add_command(label="Credits...", command=self._show_credits)

    # ------------------------------------------------------- status bar --

    def _build_statusbar(self):
        self.status = tk.Label(
            self.root, text="", anchor="w", bg="#d4d0c8",
            relief="sunken", bd=1, padx=6,
        )
        self.status.pack(side="bottom", fill="x")

    def set_status(self, text: str):
        self.status.config(text=text)

    # ------------------------------------------------------------- mdi --

    def _build_mdi(self):
        self.mdi = MdiArea(self.root)
        self.mdi.pack(fill="both", expand=True)

    def _open_startup_panels(self):
        """Calculator, Memory Walker, Message Display -- the same three
        panels beboputer_v7.main_window opens by default, tiled the
        same non-overlapping way via tile_children()."""
        specs = [
            PanelSpec(self.PANEL_TITLES["calculator"], 340, 460),
            PanelSpec(self.PANEL_TITLES["mem_walker"], 420, 460),
            PanelSpec(self.PANEL_TITLES["msg_display"], 380, 200),
        ]
        self.mdi.update_idletasks()
        children = tile_children(self.mdi, specs)
        for key, child in zip(("calculator", "mem_walker", "msg_display"), children):
            self._panels[key] = child
            self._populate_placeholder(child, key)
            child.on_close = self._make_on_close(key)

    # ------------------------------------------------ generic panel open --

    def _make_on_close(self, key):
        def _on_close():
            self._panels.pop(key, None)
        return _on_close

    def _populate_placeholder(self, child, key):
        title = self.PANEL_TITLES.get(key, key)
        frame = tk.Frame(child.content, bg="#d4d0c8")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Label(
            frame, text=title, font=("Segoe UI", 12, "bold"),
            bg="#d4d0c8", anchor="w",
        ).pack(fill="x")
        tk.Label(
            frame, text=PLACEHOLDER_NOTE, font=("Segoe UI", 9),
            bg="#d4d0c8", anchor="nw", justify="left",
        ).pack(fill="both", expand=True, pady=(8, 0))

    def _open_panel(self, key, width=360, height=280):
        """Open (or re-raise, if already open) the placeholder MdiChild
        for *key*. This is the pattern every real Phase 2 panel will
        follow too, just with real content built in _populate_* instead
        of the placeholder."""
        existing = self._panels.get(key)
        if existing is not None and existing.winfo_exists():
            existing.raise_child()
            return
        title = self.PANEL_TITLES[key]
        child = self.mdi.add_child(title, x=40, y=40, width=width, height=height)
        self._panels[key] = child
        self._populate_placeholder(child, key)
        child.on_close = self._make_on_close(key)

    # ---------------------------------------------------- menu handlers --
    # Panels: open/raise a placeholder MdiChild (real content in Phase 2).

    def _show_calculator(self):    self._open_panel("calculator", 340, 460)
    def _show_mem_walker(self):    self._open_panel("mem_walker", 420, 460)
    def _show_msg_display(self):   self._open_panel("msg_display", 380, 200)
    def _show_cpu(self):           self._open_panel("cpu")
    def _show_terminal(self):      self._open_panel("terminal")
    def _show_ports(self):         self._open_panel("ports")
    def _show_disassembler(self):  self._open_panel("disassembler", 480, 360)
    def _show_eprom(self):         self._open_panel("eprom")
    def _show_keyboard(self):      self._open_panel("keyboard")
    def _show_workbench(self):     self._open_panel("workbench")
    def _show_compiler(self):      self._open_panel("compiler", 640, 480)

    def _find_address(self):
        self._not_yet("Find Address")

    # File / Setup: not wired to real CPU/project state yet (Phase 2+).

    def _new_project(self):        self._not_yet("New Project")
    def _open_project(self):       self._not_yet("Open Project")
    def _save_project(self):       self._not_yet("Save Project")
    def _save_project_as(self):    self._not_yet("Save Project As")
    def _load_ram(self):           self._not_yet("Load RAM")
    def _save_ram(self):           self._not_yet("Save RAM")
    def _purge_ram(self):          self._not_yet("Purge RAM")
    def _set_clock(self):          self._not_yet("System Clock")
    def _load_button_file(self):   self._not_yet("Load Button File")
    def _save_button_file(self):   self._not_yet("Save Button File")
    def _restore_defaults(self):   self._not_yet("Restore Defaults")
    def _show_help(self):          self._not_yet("Help")
    def _show_web(self):           self._not_yet("DIY Calculator on the web")
    def _show_credits(self):       self._not_yet("Credits")

    def _not_yet(self, feature: str):
        messagebox.showinfo(
            feature,
            f"{feature} isn't wired up yet in the tkinter build.\n\n"
            f"This is Phase 1 (app shell) of the migration -- see "
            f"TKINTER_MIGRATION.md for what's next.",
        )
        self.set_status(f"{feature}: not yet implemented (Phase 1 build)")

    def _show_about(self):
        messagebox.showinfo(
            "About",
            f"PY-DIYCALCULATOR  v{__version__}\n\n"
            f"tkinter Phase 1 build -- app shell only.\n"
            f"See TKINTER_MIGRATION.md for migration status.",
        )

    def _exit(self):
        self.root.quit()
        self.root.destroy()
