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
Workbench 1, Keyboard, EPROM Burner, System Clock, About, and (new,
see below) Control Panel.

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
STEP / HALT / RESET + bus display + switches) is actually DEAD CODE in
the current Qt app -- it exists but main_window.py never instantiates
it (see REFACTORING_NOTES.md sec. 2, which flags this as an open
"wire it in, or delete" decision the Qt codebase hasn't made). Control
Panel is wired in here as a clearly-labeled NEW addition (implementing
REFACTORING_NOTES.md's "Option A") -- new capability, not a parity
port, called out as such in the Tools menu label.
"""

from __future__ import annotations

import os
import random
import tkinter as tk
from tkinter import messagebox, filedialog

from .mdi import MdiArea, MdiChild, PanelSpec, tile_children
from .panels.message_display import MessageDisplay
from .panels.port_monitor import PortMonitor
from .panels.control_panel import ControlPanel
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
        "control":       "Control Panel  [new]",
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        self._panels: dict[str, MdiChild] = {}  # menu_key -> MdiChild

        # -- CPU + instruction-message decoder, same as beboputer_v7 ------
        self.cpu = CPU()
        self._instr_msgs = InstructionMessages()
        self._clock_hz = 100          # simulated Hz (ticks/sec), same default
        self._run_after_id = None     # tkinter's .after() handle for the run loop
        self.msg_display: MessageDisplay | None = None
        self.port_mon: PortMonitor | None = None
        self.control_panel: ControlPanel | None = None
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
        self.msg_display.message("tkinter build -- Load RAM..., then Control Panel to Run/Step.")

        self.set_status("Ready")

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
        # at all, so they fell back to Tk's small default). option_add
        # here applies to the menu bar AND every cascaded submenu created
        # below in one shot, rather than repeating font= on each tk.Menu().
        self.root.option_add("*Menu.font", ("Segoe UI", 12))

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
        tm.add_separator()
        tm.add_command(label="Control Panel  [new -- see About]",
                        command=self._show_control_panel)

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
        same non-overlapping way via tile_children(). Message Display
        gets real content immediately; Calculator/Memory Walker are
        still placeholders (later Phase 2 slices)."""
        specs = [
            PanelSpec(self.PANEL_TITLES["calculator"], 340, 460),
            PanelSpec(self.PANEL_TITLES["mem_walker"], 420, 460),
            PanelSpec(self.PANEL_TITLES["msg_display"], 380, 220),
        ]
        self.mdi.update_idletasks()
        children = tile_children(self.mdi, specs)
        for key, child in zip(("calculator", "mem_walker", "msg_display"), children):
            self._panels[key] = child
            self._populate(child, key)
            child.on_close = self._make_on_close(key)

    # ------------------------------------------------ generic panel open --

    def _make_on_close(self, key):
        def _on_close():
            self._panels.pop(key, None)
            if key == "msg_display":
                self.msg_display = None
            elif key == "ports":
                self.port_mon = None
            elif key == "control":
                self.control_panel = None
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

    def _populate_calculator(self, child):
        self.calculator = Calculator(child.content, host_main=self)
        self.calculator.pack(fill="both", expand=True)
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

    def _populate_cpu(self, child):
        self.cpu_panel = CPUPanel(child.content, self.cpu)
        self.cpu_panel.pack(fill="both", expand=True)

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

    def _populate_keyboard(self, child):
        panel = KeyboardPanel(
            child.content, self.cpu,
            terminal_cb=self.terminal.write_char if self.terminal is not None else None,
        )
        panel.pack(fill="both", expand=True)

    def _populate_control(self, child):
        self.control_panel = ControlPanel(
            child.content,
            on_run=self._do_run, on_step=self._do_step,
            on_halt=self._do_halt, on_reset=self._do_reset,
        )
        self.control_panel.pack(fill="both", expand=True)
        self.control_panel.set_bus(self.cpu.pc, self.cpu.ram[self.cpu.pc])

    def _open_panel(self, key, width=360, height=280):
        """Open (or re-raise, if already open) the MdiChild for *key*,
        with real content if a _populate_<key> builder exists, else the
        Phase 1 placeholder."""
        existing = self._panels.get(key)
        if existing is not None and existing.winfo_exists():
            existing.raise_child()
            return
        title = self.PANEL_TITLES[key]
        child = self.mdi.add_child(title, x=40, y=40, width=width, height=height)
        self._panels[key] = child
        self._populate(child, key)
        child.on_close = self._make_on_close(key)

    # ---------------------------------------------------- menu handlers --

    def _show_calculator(self):    self._open_panel("calculator", 340, 460)
    def _show_mem_walker(self):    self._open_panel("mem_walker", 420, 460)
    def _show_msg_display(self):   self._open_panel("msg_display", 380, 220)
    def _show_cpu(self):           self._open_panel("cpu")
    def _show_terminal(self):      self._open_panel("terminal")
    def _show_ports(self):         self._open_panel("ports", 420, 340)
    def _show_disassembler(self):  self._open_panel("disassembler", 480, 360)
    def _show_eprom(self):
        # A fresh EpromBurner dialog every time -- same as Qt, no state
        # persists between opens (see EpromBurner's docstring).
        EpromBurner(
            self.root, self.cpu, on_ram_changed=self._refresh_all,
            calculator=self.calculator,
        )

    def _show_keyboard(self):      self._open_panel("keyboard", 460, 260)
    def _show_workbench(self):     self._open_panel("workbench", 420, 260)
    def _show_compiler(self):      self._open_panel("compiler", 640, 480)
    def _show_control_panel(self): self._open_panel("control", 340, 320)

    def _find_address(self):
        from tkinter import simpledialog
        txt = simpledialog.askstring("Find Address", "Enter hex address:", parent=self.root)
        if txt is None:
            return
        try:
            addr = int(txt, 16)
        except ValueError:
            messagebox.showerror("Find Address", f"Not a valid hex address: {txt!r}")
            return
        if self.mem_walker is not None:
            self.mem_walker._base = addr & 0xFFF0
            self.mem_walker.addr_var.set(f"{self.mem_walker._base:04X}")
            self.mem_walker._user_nav = True
            self.mem_walker.grid.refresh()
        else:
            self._show_mem_walker()
            if self.mem_walker is not None:
                self.mem_walker._base = addr & 0xFFF0
                self.mem_walker.addr_var.set(f"{self.mem_walker._base:04X}")
                self.mem_walker._user_nav = True
                self.mem_walker.grid.refresh()

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
        if self.control_panel is not None:
            self.control_panel.set_bus(self.cpu.pc, self.cpu.ram[self.cpu.pc])
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

    def _new_project(self):
        if messagebox.askyesno("New Project", "Clear all RAM and reset CPU?"):
            self.cpu.ram = bytearray(self.cpu.RAM_SIZE)
            self._do_reset()

    def _open_project(self):       self._load_ram()

    def _save_project(self):
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

    def _save_project_as(self):    self._save_project()
    def _save_ram(self):           self._save_project()

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
