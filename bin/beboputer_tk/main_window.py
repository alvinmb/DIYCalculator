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
main_window.py -- tkinter shell for PY-DIYCALCULATOR.

Phase 1 built the navigable app skeleton (menu bar, status bar,
MdiArea, non-overlapping startup layout). Phase 2 (parts 1-6) wires up
a real CPU instance -- same keypad read/write hooks as
beboputer_v7.main_window -- and replaces every panel/dialog with real,
working content: Message Display, Port Map Status, Calculator (full
DIYButton grid, defbuttons.ini load/save, power on/off with
random-RAM-fill matching real SRAM power-up behaviour), Memory Walker
(256-row scrollable grid, single step, breakpoints, RUN to BP, Walk
64K), CPU Registers, Terminal, Disassembler, Assembler/Editor,
Workbench 1, Keyboard, EPROM Burner, System Clock, and About.

Every File/Setup/Display/Memory/Tools/Help menu item is now wired to
real behaviour. The only remaining _not_yet() fallbacks are defensive
-- Load/Save Button File and Restore Defaults delegate to the
Calculator instance, so they only fall back to "not yet" in the
unreachable-in-practice case where the Calculator startup panel has
been closed (see TKINTER_MIGRATION.md for the handful of deliberately
out-of-scope gaps: printing, sound, Font dialog, inline Memory Walker
DATA-cell editing, multi-monitor geometry).

Menu structure (labels, grouping, and order) is copied directly from
beboputer_v7/menus.py so the tkinter build feels like the same app
from the moment you open it, not a stripped-down cousin.

The CPU engine, assembler, defbuttons.ini format, and resource_path()
are all reused unchanged -- see TKINTER_MIGRATION.md sec. 1.

Note on Control Panel: beboputer_v7/panels/control_panel.py (RUN /
STEP / HALT / RESET + bus display + switches) is DEAD CODE in the
current Qt app -- it exists but main_window.py never instantiates it
(see REFACTORING_NOTES.md sec. 2). An earlier revision of this
tkinter build wired it in as a new addition (REFACTORING_NOTES.md's
"Option A"), but it was removed (2026-08-02) as unneeded -- RUN/STEP/
HALT/RESET are already reachable via the Calculator's own Step/Run
buttons and Memory Walker's RUN to BP / STEP controls, so the extra
panel was redundant.
"""

from __future__ import annotations

import base64
import json
import os
import random
import tkinter as tk
from tkinter import messagebox, filedialog

from .mdi import MdiArea, MdiChild, PanelSpec, tile_children, retile_children, TITLE_H
from .panels.message_display import MessageDisplay
from .panels.port_monitor import PortMonitor
from .panels.calculator import Calculator
from .panels.memory_walker import MemoryWalker
from .panels.cpu_panel import CPUPanel
from .panels.terminal import Terminal
from .panels.disassembler import DisassemblerPanel
from .panels.compiler import CompilerPanel
from .panels.workbench import WorkbenchPanel
from .panels.keyboard import KeyboardPanel
from .dialogs.eprom_burner import EpromBurner
from .dialogs.system_clock import ask_hz
from .dialogs.about import AboutDialog

try:
    from beboputer_v7 import __version__
except ImportError:  # pragma: no cover - shouldn't happen once packaged
    __version__ = "0.0.0-dev"

try:
    from beboputer_v7.styles import C
except ImportError:  # pragma: no cover
    C = {"bg": "#c0c0c0", "grey": "#606060"}

from beboputer_v7.cpu import CPU
from beboputer_v7.instruction_messages import InstructionMessages

try:
    from beboputer_v7.constants import FLAG_I
except ImportError:  # pragma: no cover
    FLAG_I = 16


PLACEHOLDER_NOTE = (
    "This panel is a Phase 1 placeholder.\n\n"
    "Real content lands in a later slice of Phase 2 --\n"
    "see TKINTER_MIGRATION.md for the sequencing."
)


class BebopMain:
    """tkinter counterpart of beboputer_v7.main_window.BebopMain."""

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

        # -- CPU + instruction-message decoder, same as beboputer_v7 ------
        self.cpu = CPU()
        self._instr_msgs = InstructionMessages()
        self._clock_hz = 100          # simulated Hz (ticks/sec), same default
        self._run_after_id = None     # tkinter's .after() handle for the run loop
        self._project_path = None     # last Open/Save Project path -- Save reuses it
        self.msg_display: MessageDisplay | None = None
        self.port_mon: PortMonitor | None = None
        self.calculator: Calculator | None = None
        self.mem_walker: MemoryWalker | None = None
        self.cpu_panel: CPUPanel | None = None
        self.terminal: Terminal | None = None
        self.disassembler: DisassemblerPanel | None = None
        self.workbench: WorkbenchPanel | None = None

        root.title(f"PY-DIYCALCULATOR  v{__version__}  (tkinter)")
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
        self._wire_keypad_hooks()

        self.msg_display.message("PY-DIYCALCULATOR")
        self.msg_display.message(
            f"RAM: {self.cpu.RAM_SIZE // 1024}KB  |  Clock: {self._clock_hz}Hz (simulated)"
        )
        self.msg_display.message("tkinter build -- Load RAM..., then Memory Walker or the Calculator's Step/Run buttons.")

        self.set_status("Ready")

        # Some Linux window managers (seen on a Raspberry Pi 5 running
        # Raspberry Pi OS's default compositor) accept the "zoomed" request
        # above without raising a TclError, but never actually resize the
        # window to fill the screen -- and because the WM still considers
        # it "maximized" regardless, it also refuses to let the user drag
        # it. The window is left stuck at its un-zoomed 1200x800 size,
        # usually centred on screen, with no way to move it. Checked and
        # fixed via root.after() below -- scheduled to run once the normal
        # event loop is already pumping and every widget above is already
        # built and mapped, instead of forcing a synchronous root.update()
        # here mid-construction (before the menu bar/MDI area/panels exist),
        # which risks the WM/compositor realizing the toplevel in a
        # half-built state -- that was found to be the cause of a follow-on
        # bug where the custom Menubutton dropdowns stopped posting at all.
        root.after(150, self._ensure_window_not_stuck_centered)

    def _ensure_window_not_stuck_centered(self):
        """See the root.after() call in __init__ for the why. If "zoomed"
        didn't actually resize the window to the screen, drop back to
        "normal" state and size it manually instead -- a plain draggable/
        resizable window rather than one the WM has wedged into an
        unmovable "maximized" state."""
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        if self.root.winfo_width() < sw - 40 or self.root.winfo_height() < sh - 80:
            try:
                self.root.state("normal")
            except tk.TclError:
                pass
            self.root.geometry(f"{sw}x{sh}+0+0")

    # ------------------------------------------------------ keypad hooks --

    def _wire_keypad_hooks(self):
        """Same two hooks as beboputer_v7.main_window.__init__: a
        read-clear strobe on $F011 (each key value is seen exactly
        once by a polling program), and a write hook that forwards
        every keypress to the Port Monitor (when open) before that
        strobe wipes it, plus the CE/Clear-clears-display shortcut."""

        def _keypad_read_hook(val):
            if val != 0xFF:
                self.cpu.ram[0xF011] = 0xFF
        self.cpu._read_hooks[0xF011] = _keypad_read_hook

        def _keypad_write_hook(val):
            if self.port_mon is not None:
                self.port_mon.on_key_press(val)
            if val in (0x10, 0x11):  # CE or Clear
                self.cpu._write(0xF031, 0x10)  # send CLRCODE to display
        self.cpu._write_hooks[0xF011] = _keypad_write_hook

    # ------------------------------------------------------------ menu --

    def _build_menu(self):
        # tk.Menu widgets don't pick up any of the font bumps applied
        # elsewhere in the UI (they were never given an explicit font=
        # at all, so they fell back to Tk's small default).
        #
        # A NATIVE menu bar (root.config(menu=...)) is drawn by the OS
        # on Windows -- and Windows ignores Tk's -font option on the
        # top-level bar labels themselves, even though it happens to
        # honor -font on the cascaded dropdown popups (a real, reported
        # split: the pulldowns got bigger, the "File/Setup/..." bar
        # text didn't -- because only the dropdowns are Tk-drawn, the
        # bar itself is OS chrome). There is no supported way to force
        # a bigger font onto that native bar from Tk.
        #
        # Fix: don't use a native menu bar at all. Build the bar out of
        # plain tk.Menubutton widgets in a tk.Frame instead -- the same
        # technique already used for the Compiler panel's internal
        # File/Edit/Insert row. Every pixel of it is then normal Tk
        # drawing, so font= is fully honored on both the bar and its
        # dropdowns, on every platform, not just where the OS allows it.
        MENU_FONT = ("Segoe UI", 15)
        self.root.option_add("*Menu.font", MENU_FONT)

        bar = tk.Frame(self.root, bg="#d4d0c8", bd=1, relief="raised")
        bar.pack(side="top", fill="x")
        self._menubar_frame = bar

        def _menu(label):
            """Add one top-level Menubutton to the bar and return its
            (empty) dropdown Menu for the caller to populate.

            Deliberately NOT using tk.Menubutton's built-in automatic
            posting (the ``menu=submenu`` option) -- on a Raspberry Pi 5
            that left only the FIRST menu in the bar (File) responding to
            a click at all; every one built after it (Setup, Display,
            Memory, Tools, Help) never posted. Two follow-up attempts made
            it progressively worse:
              1. Force-releasing the grab on <Unmap> -- NO menu responded
                 afterward, including File.
              2. Posting manually via tk_popup() with an explicit
                 menu.grab_release() in a try/finally (the commonly-cited
                 tkinter FAQ idiom) -- worked at first, but once a second
                 menu bar elsewhere in the app (the Assembler/Editor
                 panel's own File/Edit/Insert row, built the same way) was
                 also exercised, the WHOLE app locked up -- not just
                 menus, every button anywhere stopped responding. tk_popup
                 already manages its own grab/ungrab internally (the same
                 underlying Tk library mechanism the automatic Menubutton
                 path also uses); our extra manual grab_release() call
                 fired essentially immediately (tk_popup doesn't block)
                 and raced Tk's own internal release, corrupting its grab
                 bookkeeping until eventually nothing could grab the
                 pointer at all.
            Fix: call tk_popup() alone and let Tk's own internal dismiss
            handling release the grab itself, same as it already does for
            the plain Menubutton case -- no manual grab management here. """
            mbut = tk.Menubutton(
                bar, text=label, font=MENU_FONT, bg="#d4d0c8",
                activebackground="#c0bdb5", relief="flat", padx=10, pady=3,
            )
            submenu = tk.Menu(bar, tearoff=0, font=MENU_FONT)
            mbut.pack(side="left")

            def _post(event):
                submenu.tk_popup(mbut.winfo_rootx(),
                                  mbut.winfo_rooty() + mbut.winfo_height())
            mbut.bind("<Button-1>", _post)
            return submenu

        # ── File ─────────────────────────────────────────────────────────
        fm = _menu("File")
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
        sm = _menu("Setup")
        sm.add_command(label="System Clock...",   command=self._set_clock)
        sm.add_separator()
        # Interrupt -- a standalone "⚡ Interrupt" toolbar button in the Qt
        # version (main_window.py's _build_toolbar()/_do_interrupt()); this
        # tkinter build has no toolbar, so it lives here in Setup instead.
        sm.add_command(label="Interrupt",           command=self._do_interrupt)
        sm.add_separator()
        sm.add_command(label="Load Button File...", command=self._load_button_file)
        sm.add_command(label="Save Button File...", command=self._save_button_file)
        sm.add_command(label="Restore Defaults",    command=self._restore_defaults)

        # ── Display ──────────────────────────────────────────────────────
        dm = _menu("Display")
        dm.add_command(label="CPU Registers",   command=self._show_cpu)
        dm.add_command(label="Message Display", command=self._show_msg_display)
        dm.add_command(label="Terminal",        command=self._show_terminal)
        dm.add_command(label="Port Map Status", command=self._show_ports)
        dm.add_command(label="Disassembler",    command=self._show_disassembler)

        # ── Memory ───────────────────────────────────────────────────────
        mm = _menu("Memory")
        mm.add_command(label="Memory Walker",   command=self._show_mem_walker)

        # ── Tools ────────────────────────────────────────────────────────
        tm = _menu("Tools")
        tm.add_command(label="EPROM Burner",         command=self._show_eprom)
        tm.add_command(label="Calculator...",        command=self._show_calculator)
        tm.add_command(label="Keyboard...",          command=self._show_keyboard)
        tm.add_command(label="Workbench 1...",       command=self._show_workbench)
        tm.add_command(label="Assembler / Editor...", command=self._show_compiler)

        # ── Help ─────────────────────────────────────────────────────────
        hm = _menu("Help")
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
        same non-overlapping way via tile_children(). All three get
        real content immediately.

        Calculator and Memory Walker both self-correct their real size
        after being built (_autosize_fixed_panel(), called from their
        _populate_<key>() -- font metrics/DPI vary enough across
        machines that no hardcoded width/height reliably avoids
        clipping, see TKINTER_MIGRATION.md), which can end up wider or
        narrower than tile_children()'s initial PanelSpec guess below.
        Since each later panel's x position was computed from that
        guess, a panel growing during its own autosize pass can leave a
        sibling overlapping it or squeezed into less room than it
        actually has -- so after every panel in the group has finished
        self-correcting, retile_children() lays all three out fresh
        from their real, final sizes."""
        specs = [
            PanelSpec(self.PANEL_TITLES["calculator"], 750, 380,
                      resizable=False, maximizable=False),
            PanelSpec(self.PANEL_TITLES["mem_walker"], 420, 460, fixed_width=True),
            # 25% bigger than the previous default (380x220 -> 475x275).
            PanelSpec(self.PANEL_TITLES["msg_display"], 475, 275),
        ]
        self.mdi.update_idletasks()
        children = tile_children(self.mdi, specs)
        for key, child in zip(("calculator", "mem_walker", "msg_display"), children):
            self._panels[key] = child
            self._populate(child, key)
            child.on_close = self._make_on_close(key)
        retile_children(self.mdi, children)

    # ------------------------------------------------ generic panel open --

    def _make_on_close(self, key):
        def _on_close():
            self._panels.pop(key, None)
            if key == "msg_display":
                self.msg_display = None
            elif key == "ports":
                self.port_mon = None
            elif key == "calculator":
                self.calculator = None
            elif key == "mem_walker":
                self.mem_walker = None
            elif key == "cpu":
                self.cpu_panel = None
            elif key == "terminal":
                self.terminal = None
            elif key == "disassembler":
                self.disassembler = None
            elif key == "workbench":
                self.workbench = None
        return _on_close

    def _populate(self, child, key):
        """Dispatch to a real panel builder if one exists for *key*,
        else fall back to the Phase 1 placeholder."""
        builder = getattr(self, f"_populate_{key}", None)
        if builder is not None:
            builder(child)
        else:
            self._populate_placeholder(child, key)

    def _populate_placeholder(self, child, key):
        title = self.PANEL_TITLES.get(key, key)
        frame = tk.Frame(child.content, bg="#d4d0c8")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Label(
            frame, text=title, font=("Segoe UI", 15, "bold"),
            bg="#d4d0c8", anchor="w",
        ).pack(fill="x")
        tk.Label(
            frame, text=PLACEHOLDER_NOTE, font=("Segoe UI", 12),
            bg="#d4d0c8", anchor="nw", justify="left",
        ).pack(fill="both", expand=True, pady=(8, 0))

    def _populate_msg_display(self, child):
        self.msg_display = MessageDisplay(child.content)
        self.msg_display.pack(fill="both", expand=True)

    def _populate_ports(self, child):
        self.port_mon = PortMonitor(child.content, self.cpu)
        self.port_mon.pack(fill="both", expand=True)
        self.port_mon.refresh()
        # Same fixed-size-to-real-content treatment as the calculator --
        # see _autosize_fixed_panel()'s docstring. _show_ports() opens
        # this panel with resizable=False, maximizable=False.
        self._autosize_fixed_panel(child, self.port_mon)

    def _populate_calculator(self, child):
        # The calculator's button grid has a real minimum size (driven by
        # its labels' text at the current font) that this code can't
        # know in advance on every machine -- font metrics and DPI
        # scaling vary enough across Windows/Linux/Mac (and monitor
        # scaling settings) that no single fixed MdiChild width/height
        # reliably avoids clipping on every screen. Rather than keep
        # guessing pixel constants, the calculator lives inside a
        # scrolling Canvas: when the MdiChild window is roomy enough,
        # the calculator stretches to fill it exactly like before
        # (buttons expand via their uniform grid weighting); when the
        # window is smaller than the calculator's natural size, the
        # mouse wheel still scrolls it into view instead of anything
        # being cut off and unreachable.
        #
        # No visible Scrollbar widgets, by request -- _autosize_fixed_panel()
        # below snaps the MdiChild to the calculator's exact built size
        # immediately after creation, so there's normally nothing to scroll;
        # the always-on scrollbar track was just clutter around a panel that
        # never actually needed to move. The canvas/scrollregion machinery
        # (and the mouse-wheel binding) stays in place as an invisible
        # fallback for the rare case a window manager can't honor the full
        # requested size (e.g. a screen too small to fit it).
        container = tk.Frame(child.content, bg="#c0c0c0")
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg="#c0c0c0", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        self.calculator = Calculator(canvas, host_main=self)

        # Snap the (fixed-size, resizable=False) MdiChild to the
        # calculator's real built size on THIS machine, then it stays
        # locked at that size -- see _autosize_fixed_panel(). The
        # scrolling canvas above stays in place as a defensive fallback
        # (e.g. if a future label/font change grows the content again),
        # but with an exact fit there should be nothing to scroll.
        self._autosize_fixed_panel(child, self.calculator, pad_w=40, pad_h=20)

        win_id = canvas.create_window((0, 0), window=self.calculator, anchor="nw")

        def _sync_scrollregion(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.calculator.bind("<Configure>", _sync_scrollregion)

        def _sync_canvas_size(event):
            min_w = self.calculator.winfo_reqwidth()
            min_h = self.calculator.winfo_reqheight()
            canvas.itemconfigure(
                win_id,
                width=max(event.width, min_w),
                height=max(event.height, min_h),
            )
        canvas.bind("<Configure>", _sync_canvas_size)

        def _mousewheel(event):
            canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        for w in (canvas, self.calculator):
            w.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _mousewheel))
            w.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Same two write hooks as beboputer_v7.main_window: $F031 (display)
        # and $F032 (LEDs) are driven purely by whatever a running program
        # writes to those ports -- the calculator has no built-in expression
        # evaluator (see panels/calculator.py's module docstring).
        self.cpu._write_hooks[0xF031] = self.calculator.write_display
        self.cpu._write_hooks[0xF032] = self.calculator.write_leds

    def _populate_mem_walker(self, child):
        self.mem_walker = MemoryWalker(
            child.content, self.cpu,
            on_step_executed=self._on_mem_walker_step,
            on_bp_hit=self._on_mem_walker_bp_hit,
        )
        self.mem_walker.pack(fill="both", expand=True)
        # Width is fixed to the row layout's real content width (same
        # clipping-avoidance reasoning as _autosize_fixed_panel()'s other
        # callers); height stays freely resizable -- fix_height=False --
        # so more/fewer memory rows can be shown, via a vertical-only
        # grip (_show_mem_walker() opens with fixed_width=True).
        self._autosize_fixed_panel(child, self.mem_walker, fix_height=False)

    def _populate_cpu(self, child):
        self.cpu_panel = CPUPanel(child.content, self.cpu)
        self.cpu_panel.pack(fill="both", expand=True)
        # Same fixed-size-to-real-content treatment as the calculator --
        # see _autosize_fixed_panel()'s docstring. _show_cpu() opens
        # this panel with resizable=False, maximizable=False.
        self._autosize_fixed_panel(child, self.cpu_panel)

    def _populate_terminal(self, child):
        self.terminal = Terminal(child.content)
        self.terminal.pack(fill="both", expand=True)
        # Same $F028 write hook as beboputer_v7.main_window: any
        # STORE ($F028), A instruction routes ACC straight to the screen.
        self.cpu._write_hooks[0xF028] = self.terminal.write_char
        # Terminal follows the calculator's power state, same as Qt.
        if self.calculator is not None:
            self.terminal.set_power(self.calculator.powered)

    def _populate_disassembler(self, child):
        self.disassembler = DisassemblerPanel(child.content, self.cpu)
        self.disassembler.pack(fill="both", expand=True)
        self.disassembler.refresh_at_pc(self.cpu.pc)

    def _populate_compiler(self, child):
        panel = CompilerPanel(child.content, host_main=self)
        panel.pack(fill="both", expand=True)

    def _populate_workbench(self, child):
        self.workbench = WorkbenchPanel(child.content, self.cpu)
        self.workbench.pack(fill="both", expand=True)
        powered = self.calculator.powered if self.calculator is not None else False
        self.workbench.set_power(powered)
        self.workbench.sync_from_ram()
        # Same fixed-size-to-real-content treatment as Calculator/CPU
        # Registers/Port Map/Keyboard/Control Panel -- see
        # _autosize_fixed_panel()'s docstring. _show_workbench() opens
        # this panel with resizable=False, maximizable=False.
        self._autosize_fixed_panel(child, self.workbench)

    def _populate_keyboard(self, child):
        panel = KeyboardPanel(
            child.content, self.cpu,
            terminal_cb=self.terminal.write_char if self.terminal is not None else None,
        )
        panel.pack(fill="both", expand=True)
        # Same fixed-size-to-real-content treatment as the calculator --
        # see _autosize_fixed_panel()'s docstring. _show_keyboard() opens
        # this panel with resizable=False, maximizable=False.
        self._autosize_fixed_panel(child, panel)

    def _open_panel(self, key, width=360, height=280,
                     resizable=True, maximizable=True, fixed_width=False):
        """Open (or re-raise, if already open) the MdiChild for *key*,
        with real content if a _populate_<key> builder exists, else the
        Phase 1 placeholder."""
        existing = self._panels.get(key)
        if existing is not None and existing.winfo_exists():
            existing.raise_child()
            return
        title = self.PANEL_TITLES[key]
        child = self.mdi.add_child(title, x=40, y=40, width=width, height=height,
                                    resizable=resizable, maximizable=maximizable,
                                    fixed_width=fixed_width)
        self._panels[key] = child
        self._populate(child, key)
        child.on_close = self._make_on_close(key)

    def _autosize_fixed_panel(self, child, content_widget, pad_w=28, pad_h=12,
                               fix_height=True):
        """Snap *child*'s width (and, unless fix_height=False, its height
        too) to the real, already-built *content_widget*'s actual
        required size, instead of trusting a hardcoded guess that may
        not match this machine's font metrics/DPI scaling.

        Called once, right after a panel's real content has been
        constructed and packed -- winfo_reqwidth/reqheight only reflect
        reality once the widget tree exists, so this can't run any
        earlier than that. pad_w/pad_h cover the MdiChild's own border +
        a small safety margin (the scrolling Canvas some fixed panels
        use for defense-in-depth doesn't need it, but a plain content
        frame like this one benefits from a few spare pixels).

        fix_height=False leaves the current height alone (the panel
        should have been opened with fixed_width=True and
        resizable=True in that case -- e.g. Memory Walker: the row
        layout has one correct width, but a user may want more or fewer
        rows visible, so height should stay user-resizable via the
        vertical-only grip).
        """
        child.update_idletasks()
        req_w = content_widget.winfo_reqwidth()
        new_w = req_w + pad_w
        # Cap against the MdiArea's total width, not "what's left to the
        # right of wherever this child currently sits" -- child.x may
        # still be a stale placeholder from an earlier layout guess
        # (e.g. tile_children() positioned this panel next to a sibling
        # that has since grown during its own autosize pass). Capping by
        # position here would needlessly shrink a panel that has plenty
        # of room once positions get corrected. For startup-tiled panels
        # that's retile_children(), called once every panel in the
        # group has finished self-correcting; a standalone _open_panel()
        # (Tools/Display menu) always opens at a fresh x=40 anyway.
        area_w = max(self.mdi.winfo_width(), new_w)
        child.width = min(new_w, area_w)
        if fix_height:
            req_h = content_widget.winfo_reqheight()
            new_h = req_h + TITLE_H + pad_h
            area_h = max(self.mdi.winfo_height(), new_h)
            child.height = min(new_h, area_h - child.y)
        child._place()

    # ---------------------------------------------------- menu handlers --

    def _show_calculator(self):
        self._open_panel("calculator", 1120, 560,
                          resizable=False, maximizable=False)
    def _show_mem_walker(self):
        self._open_panel("mem_walker", 420, 460,
                          maximizable=True, fixed_width=True)
    def _show_msg_display(self):
        # 25% bigger than the previous default (380x220 -> 475x275).
        self._open_panel("msg_display", 475, 275)
    def _show_cpu(self):
        self._open_panel("cpu", resizable=False, maximizable=False)
    def _show_terminal(self):
        # 50% larger than the previous default open size (360x280 -> 540x420).
        self._open_panel("terminal", 540, 420)
    def _show_ports(self):
        self._open_panel("ports", 420, 340, resizable=False, maximizable=False)
    def _show_disassembler(self):  self._open_panel("disassembler", 480, 360)
    def _show_eprom(self):
        # A fresh EpromBurner dialog every time -- same as Qt, no state
        # persists between opens (see EpromBurner's docstring).
        EpromBurner(
            self.root, self.cpu, on_ram_changed=self._refresh_all,
            calculator=self.calculator,
        )

    def _show_keyboard(self):
        self._open_panel("keyboard", 460, 260, resizable=False, maximizable=False)
    def _show_workbench(self):
        self._open_panel("workbench", 420, 260, resizable=False, maximizable=False)
    def _show_compiler(self):      self._open_panel("compiler", 640, 480)

    # -------------------------------------------------------- CPU ops --

    def _do_run(self):
        if self.cpu.halted:
            self.msg_display.message("CPU is HALTed. Reset first.")
            return
        self.cpu.running = True
        self.set_status("Running…")
        self._run_tick()

    def _do_halt(self):
        self.cpu.running = False
        if self._run_after_id is not None:
            self.root.after_cancel(self._run_after_id)
            self._run_after_id = None
        self.set_status(f"Halted at PC=${self.cpu.pc:04X}")
        self._refresh_all()

    def _do_step(self):
        if self._run_after_id is not None:
            self.root.after_cancel(self._run_after_id)
            self._run_after_id = None
        self.cpu.running = False
        self.cpu.step()
        self.msg_display.message(self._instr_msgs.describe(self.cpu))
        self._refresh_all()
        if self.cpu.halted:
            self.set_status("HALT instruction executed.")
            self.msg_display.message("--- HALT ---")

    def _do_interrupt(self):
        """Manually assert the interrupt mask bit (flag I) -- ported from
        Qt's toolbar '⚡ Interrupt' button / _do_interrupt(). Same effect
        as the CPU executing a SETIM instruction, but triggered from the
        UI rather than from a running program -- lets you test
        interrupt-mask-dependent code paths without having to assemble a
        SETIM into the program itself.

        Only takes effect while the calculator is switched on -- with
        the calculator off there's no powered board to interrupt, same
        reasoning as the Qt version's "must be ON" gate.
        """
        if self.calculator is None or not self.calculator.powered:
            self.msg_display.message("Interrupt ignored -- calculator is off.")
            self.set_status("Interrupt ignored -- calculator is off.")
            return
        self.cpu.flags |= FLAG_I
        self.cpu.flags_touched |= FLAG_I
        self._refresh_all()
        self.msg_display.message("⚡ Interrupt: mask bit (I) set.")
        self.set_status("Interrupt mask bit (I) set.")

    def _do_reset(self, clear_calc_display=True):
        if self._run_after_id is not None:
            self.root.after_cancel(self._run_after_id)
            self._run_after_id = None
        self.cpu.reset()
        if clear_calc_display and self.calculator is not None:
            # blank_display(), not write_display(0x10): a Reset means no
            # program is driving the display yet, so it should go truly
            # blank rather than showing "0" (same reasoning as Qt).
            self.calculator.blank_display()
        if self.port_mon is not None:
            self.port_mon.reset()
        if self.terminal is not None:
            self.terminal.clear()   # blank the terminal, if anything was printed
        if self.workbench is not None:
            self.workbench.reset()  # switches back to off position, outputs blanked
        if self.msg_display is not None:
            self.msg_display.message("↺ CPU Reset.")
        self.set_status("Reset")
        self._refresh_all()

    def _do_random_fill_ram(self):
        """Fill RAM with random bytes on power-on, matching real SRAM
        power-up behaviour (undefined garbage, not a tidy $00). Same
        logic as beboputer_v7.main_window._do_random_fill_ram()."""
        rom_end = self.cpu.ROM_END
        for i in range(rom_end):
            self.cpu.ram[i] = 0
            self.cpu.ram_touched[i] = 1
        for i in range(rom_end, self.cpu.RAM_SIZE):
            self.cpu.ram[i] = random.randint(0, 255)
            self.cpu.ram_touched[i] = 0
        self.cpu.ram[0xF011] = 0xFF
        self.cpu.ram[0xF031] = 0x00
        self.cpu.ram[0xF032] = 0x3F
        for addr in (0xF011, 0xF031, 0xF032):
            self.cpu.ram_touched[addr] = 1
        self._refresh_all()
        if self.msg_display is not None:
            self.msg_display.message(
                "Power on: RAM randomized (real hardware powers up with garbage, not zeros)."
            )

    def _do_power_off_ram(self):
        """Mark RAM undefined on power-off (not zeroed -- see
        beboputer_v7.main_window._do_power_off_ram())."""
        rom_end = self.cpu.ROM_END
        for i in range(rom_end, self.cpu.RAM_SIZE):
            self.cpu.ram_touched[i] = 0
        self._refresh_all()
        if self.msg_display is not None:
            self.msg_display.message("Power off.")

    def _on_power_changed(self, on: bool):
        """Called by Calculator.control("On/Off"). Same behaviour as
        beboputer_v7.main_window._on_power_changed()."""
        if self.terminal is not None:
            self.terminal.set_power(on)
        if self.workbench is not None:
            self.workbench.set_power(on)
        if on:
            self._do_random_fill_ram()
            self._do_reset(clear_calc_display=False)
        else:
            if self._run_after_id is not None:
                self.root.after_cancel(self._run_after_id)
                self._run_after_id = None
            self.cpu.running = False
            self._do_power_off_ram()

    def _run_tick(self):
        if self.cpu.halted:
            self._run_after_id = None
            self.cpu.running = False
            self.set_status(f"HALT at PC=${self.cpu.pc:04X}")
            self._refresh_all()
            return
        bp_hit = None
        breakpoints = self.mem_walker._breakpoints if self.mem_walker is not None else ()
        for _ in range(10):    # execute 10 instructions per tick, same as Qt build
            self.cpu.step()
            if self.cpu.halted:
                break
            # Stop on a Memory Walker breakpoint, same as its own "RUN to
            # BP" button -- without this, Run ignores breakpoints entirely
            # (see beboputer_v7.main_window._run_tick()'s equivalent check).
            if self.cpu.pc in breakpoints:
                bp_hit = self.cpu.pc
                break
        self._refresh_all()
        if self.cpu.halted:
            self.set_status(f"HALT at PC=${self.cpu.pc:04X}")
            self.msg_display.message("--- HALT ---")
            self._run_after_id = None
            return
        if bp_hit is not None:
            reason = f"BP hit at ${bp_hit:04X}"
            self.set_status(reason)
            self.msg_display.message(reason)
            self._run_after_id = None
            return
        self._run_after_id = self.root.after(
            max(1, 1000 // max(1, self._clock_hz)), self._run_tick
        )

    def _on_mem_walker_step(self, mnemonic):
        """Called after Memory Walker's own STEP column single-steps the CPU."""
        if self.msg_display is not None:
            self.msg_display.message(self._instr_msgs.describe(self.cpu))
        self._refresh_all()

    def _on_mem_walker_bp_hit(self, reason):
        """Called when Memory Walker's RUN to BP stops (BP / HALT / limit)."""
        if self.msg_display is not None:
            self.msg_display.message(reason)
        self.set_status(reason)
        self._refresh_all()

    def _refresh_all(self):
        if self.cpu_panel is not None:
            self.cpu_panel.refresh()
        if self.port_mon is not None:
            self.port_mon.refresh()
        if self.mem_walker is not None:
            self.mem_walker.highlight_pc(self.cpu.pc)
        if self.disassembler is not None:
            self.disassembler.refresh_at_pc(self.cpu.pc)

    # -------------------------------------------------------- Load RAM --

    def _load_ram(self):
        path = filedialog.askopenfilename(
            title="Load RAM",
            filetypes=[("RAM/ROM files", "*.ram *.rom"), ("All files", "*.*")],
        )
        if not path:
            return
        self._load_file(path)

    def _load_file(self, path: str):
        """Same load-address rule as beboputer_v7.main_window._load_file():
        .rom -> $0000 (boot/reset vector), .ram or anything else -> $4000
        (compiler output / user program). A file exactly RAM_SIZE bytes
        is treated as a full 64KB image."""
        ext = os.path.splitext(path)[1].lower()
        load_addr = 0x0000 if ext == ".rom" else 0x4000
        try:
            with open(path, "rb") as f:
                data = f.read()
            self.cpu.ram = bytearray(self.cpu.RAM_SIZE)
            self.cpu.ram_touched = bytearray(self.cpu.RAM_SIZE)
            if len(data) == self.cpu.RAM_SIZE:
                self.cpu.ram[:] = data
                self.cpu.ram_touched[:] = b"\x01" * self.cpu.RAM_SIZE
                msg = f"Loaded: {os.path.basename(path)}  (full 64KB image)"
                status = f"Loaded {path} (full 64KB image)"
            else:
                max_bytes = self.cpu.RAM_SIZE - load_addr
                chunk = data[:max_bytes]
                self.cpu.ram[load_addr:load_addr + len(chunk)] = chunk
                self.cpu.ram_touched[load_addr:load_addr + len(chunk)] = b"\x01" * len(chunk)
                msg = (f"Loaded: {os.path.basename(path)}  "
                       f"({len(chunk)} bytes @ ${load_addr:04X})")
                status = f"Loaded {path} @ ${load_addr:04X}"
            self._do_reset(clear_calc_display=False)
            if self.msg_display is not None:
                self.msg_display.message(msg)
            self.set_status(status)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # -- File / Setup ---------------------------------------------------------

    # A project is the whole session, not just the RAM image: which
    # panels (Calculator, Memory Walker, CPU Registers, ...) are open,
    # where they're positioned/sized, the calculator's power state, the
    # simulated clock speed, and the RAM/ram_touched contents. Saved as
    # one JSON *.prj file. This is a real, separate concept from
    # Load/Save RAM below (which only ever touch cpu.ram, no layout) --
    # they used to just alias to a raw-ROM-dump save/load, which wasn't
    # really a "project" at all.

    # Panels whose on-screen size is locked to their own content and
    # re-derived every time they're opened (_autosize_fixed_panel(),
    # called from each one's _populate_<key>()) -- restoring a saved
    # width/height for these would fight that autosize logic and risks
    # reintroducing clipping on a machine with different font metrics/
    # DPI than whatever machine the project was saved on. Only their
    # position (x, y) is restored; size is left for the panel to
    # recompute itself, exactly as a fresh Tools/Display-menu open does.
    _PROJECT_SIZE_LOCKED = {"calculator", "cpu", "ports", "keyboard", "workbench"}
    # Locked width (from the same autosize logic) but free-resizing
    # height -- only height is restored.
    _PROJECT_FIXED_WIDTH = {"mem_walker"}
    # Every other open-able panel (msg_display, terminal, disassembler,
    # compiler) is fully user-resizable, so both width and height are
    # restored along with position.

    def _capture_project_state(self) -> dict:
        panels = {
            key: {"x": child.x, "y": child.y, "width": child.width, "height": child.height}
            for key, child in self._panels.items()
        }
        return {
            "format": "beboputer-project",
            "version": 1,
            "clock_hz": self._clock_hz,
            "calculator_powered": bool(self.calculator.powered) if self.calculator is not None else False,
            "ram": base64.b64encode(bytes(self.cpu.ram)).decode("ascii"),
            "ram_touched": base64.b64encode(bytes(self.cpu.ram_touched)).decode("ascii"),
            "panels": panels,
        }

    def _apply_project_state(self, data: dict):
        # 1. A project restores an exact arrangement, not a merge with
        #    whatever happens to already be open -- close everything first.
        for child in list(self._panels.values()):
            child.close()
        self._panels.clear()

        # 2. Reopen exactly the panels the project had open, each via its
        #    normal _show_<key>() so every panel's usual flags/autosize
        #    logic runs exactly as it does for a manual menu open. A
        #    project file saved before Control Panel was removed
        #    (2026-08-02) may still have a "control" entry -- there's no
        #    _show_control method (getattr's default) so it's silently
        #    skipped rather than reopening a panel that no longer exists.
        saved_panels = data.get("panels", {})
        for key in saved_panels:
            show = getattr(self, f"_show_{key}", None)
            if callable(show):
                show()

        # 3. Calculator power state must be set *before* the RAM restore
        #    below -- Calculator.control("On/Off") turning power ON runs
        #    _do_random_fill_ram() + a reset as a side effect (real-
        #    hardware "garbage RAM at power-on" behaviour, see
        #    _on_power_changed()), which would immediately clobber the
        #    saved RAM if it ran afterward instead.
        want_powered = bool(data.get("calculator_powered", False))
        if self.calculator is not None and self.calculator.powered != want_powered:
            self.calculator.control("On/Off")

        # 4. Now restore RAM/clock, overwriting any power-on random fill.
        try:
            raw = base64.b64decode(data.get("ram", ""))
            if len(raw) == self.cpu.RAM_SIZE:
                self.cpu.ram = bytearray(raw)
            raw_t = base64.b64decode(data.get("ram_touched", ""))
            if len(raw_t) == self.cpu.RAM_SIZE:
                self.cpu.ram_touched = bytearray(raw_t)
        except (ValueError, TypeError):
            pass  # corrupt/foreign base64 -- leave whatever RAM state we already have
        self._clock_hz = int(data.get("clock_hz", self._clock_hz))
        self._do_reset(clear_calc_display=False)

        # 5. Finally, snap every reopened panel to its saved position
        #    (and, for panels whose size isn't autosize-locked, its
        #    saved size too -- see _PROJECT_* sets above).
        for key, geo in saved_panels.items():
            child = self._panels.get(key)
            if child is None:
                continue
            child.x = geo.get("x", child.x)
            child.y = geo.get("y", child.y)
            if key not in self._PROJECT_SIZE_LOCKED:
                child.height = geo.get("height", child.height)
                if key not in self._PROJECT_FIXED_WIDTH:
                    child.width = geo.get("width", child.width)
            child._place()

        self._refresh_all()

    def _write_project_file(self, path: str):
        try:
            data = self._capture_project_state()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self._project_path = path
            if self.msg_display is not None:
                self.msg_display.message(f"Project saved: {os.path.basename(path)}")
            self.set_status(f"Project saved: {path}")
        except Exception as e:
            messagebox.showerror("Save Project failed", str(e))

    def _new_project(self):
        if messagebox.askyesno(
            "New Project",
            "Clear all RAM, reset the CPU, and close all panels back to "
            "the default layout?",
        ):
            self.cpu.ram = bytearray(self.cpu.RAM_SIZE)
            self.cpu.ram_touched = bytearray(self.cpu.RAM_SIZE)
            for child in list(self._panels.values()):
                child.close()
            self._panels.clear()
            self._project_path = None
            self._open_startup_panels()
            self._do_reset()

    def _open_project(self):
        path = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[("Beboputer Project", "*.prj"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("format") != "beboputer-project":
                raise ValueError("Not a Beboputer project file.")
        except Exception as e:
            messagebox.showerror("Open Project failed", str(e))
            return
        self._apply_project_state(data)
        self._project_path = path
        if self.msg_display is not None:
            self.msg_display.message(f"Project opened: {os.path.basename(path)}")
        self.set_status(f"Project opened: {path}")

    def _save_project(self):
        if self._project_path:
            self._write_project_file(self._project_path)
        else:
            self._save_project_as()

    def _save_project_as(self):
        path = filedialog.asksaveasfilename(
            title="Save Project As", defaultextension=".prj",
            filetypes=[("Beboputer Project", "*.prj"), ("All files", "*.*")],
        )
        if not path:
            return
        self._write_project_file(path)

    def _save_ram(self):
        path = filedialog.asksaveasfilename(
            title="Save ROM", defaultextension=".rom",
            filetypes=[("ROM Files", "*.rom"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "wb") as f:
                f.write(bytes(self.cpu.ram))
            if self.msg_display is not None:
                self.msg_display.message(f"Saved: {os.path.basename(path)}")
            self.set_status(f"Saved: {path}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def _purge_ram(self):
        if messagebox.askyesno("Purge RAM", "Zero all 64KB of RAM?"):
            self._do_purge_ram()

    def _do_purge_ram(self):
        """Zero all RAM in-place and restore I/O sentinels. Every byte is
        now a known, deterministic value ($00), so mark all of RAM as
        "touched" -- Memory Walker should display $00, not the
        undefined-garbage placeholder ($XX). Same as beboputer_v7's
        _do_purge_ram()."""
        for i in range(self.cpu.RAM_SIZE):
            self.cpu.ram[i] = 0
            self.cpu.ram_touched[i] = 1
        self.cpu.ram[0xF011] = 0xFF
        self.cpu.ram[0xF031] = 0x00
        self.cpu.ram[0xF032] = 0x00
        self._refresh_all()
        if self.msg_display is not None:
            self.msg_display.message("RAM purged.")
        self.set_status("RAM purged.")

    def _set_clock(self):
        new_hz = ask_hz(self.root, self._clock_hz)
        if new_hz is not None:
            self._clock_hz = new_hz
            self.set_status(f"Clock set to {new_hz} Hz")
            if self.msg_display is not None:
                self.msg_display.message(f"System clock set to {new_hz} Hz.")

    def _load_button_file(self):
        if self.calculator is not None:
            self.calculator._load_button_file()
        else:
            self._not_yet("Load Button File")

    def _save_button_file(self):
        if self.calculator is not None:
            self.calculator._save_button_file()
        else:
            self._not_yet("Save Button File")

    def _restore_defaults(self):
        if self.calculator is not None:
            self.calculator._restore_defaults()
            self.set_status("Button definitions restored to defaults.")
        else:
            self._not_yet("Restore Defaults")

    def _show_help(self):
        """Open the HTML help file in the system default browser, same
        source/bundle path logic as beboputer_v7.main_window._show_help()."""
        import sys as _sys
        import webbrowser
        if getattr(_sys, "frozen", False):
            try:
                from beboputer_v7.paths import resource_path
                help_path = resource_path("beboputer_v7_help.html")
            except ImportError:
                help_path = os.path.join(os.path.dirname(__file__), "..", "beboputer_v7_help.html")
        else:
            help_path = os.path.normpath(
                os.path.join(os.path.dirname(__file__), "..", "beboputer_v7_help.html")
            )
        if os.path.exists(help_path):
            webbrowser.open(f"file:///{help_path.replace(os.sep, '/')}")
        else:
            messagebox.showinfo("Help", f"Help file not found:\n{help_path}")

    def _show_web(self):
        import webbrowser
        webbrowser.open("https://www.clivemaxfield.com/diycalculator/index.shtml")

    def _show_credits(self):
        messagebox.showinfo(
            "The Crew....",
            "PY-DIYCALCULATOR\n\n"
            "by Clive 'Max' Maxfield & Alvin Brown\n"
            "Python/tkinter port\n\n"
            "Assembler based on DAS by David Venhoek\n\n",
        )

    def _not_yet(self, feature: str):
        messagebox.showinfo(
            feature,
            f"{feature} isn't wired up yet in the tkinter build.\n\n"
            f"See TKINTER_MIGRATION.md for what's next.",
        )
        self.set_status(f"{feature}: not yet implemented")

    def _show_about(self):
        AboutDialog(self.root)

    def _exit(self):
        self.root.quit()
        self.root.destroy()
