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

"""Memory Walker -- scrollable memory dump with single-step + breakpoints.

tkinter port of beboputer_v7/panels/memory_walker.py, built on top of
memory_grid.py (promoted from the Phase 0 spike). Same feature set:

  - BP column: click a row to toggle a breakpoint (absolute RAM address,
    stored in self._breakpoints -- a plain set, inspectable by
    main_window.py exactly like the Qt build inspects mem_walker._breakpoints
    during Run).
  - STEP column: click any cell in that column to single-step the CPU.
  - RUN to BP: steps the CPU until PC hits a breakpoint, the CPU HALTs,
    or RUN_LIMIT is reached.
  - Walk 64K: continuously pages through the full address space.
  - GO / Go to PC: manual navigation vs. PC-following, same _user_nav
    flag semantics as Qt (manual nav suspends PC-following until you
    explicitly step again or click Go to PC).

Callback parameters (on_step_executed, on_bp_hit) replace Qt's
step_executed/bp_hit pyqtSignals -- same reasoning as every other panel
ported this session: a single-widget-to-single-handler wire-up doesn't
need a signal/slot layer in tkinter.

NOT ported in this slice: double-click-to-edit-DATA-cell (Qt's
QTableWidget supports inline cell editing; the Text-based grid here
would need a floating Entry-on-click overlay to match, which is real
UI work rather than a mechanical port -- RAM can still be changed by
loading a new .ram/.rom via File > Load RAM). ideal_width() (Qt-only:
computed the QMdiSubWindow's initial size from exact column pixel
widths) has no tkinter equivalent need -- MdiChild panels are already
sized via PanelSpec/tile_children().
"""

from __future__ import annotations

import tkinter as tk

from .memory_grid import MemoryGrid

try:
    from beboputer_v7.constants import RUN_LIMIT
except ImportError:  # pragma: no cover
    RUN_LIMIT = 500_000

try:
    from beboputer_v7.styles import C
except ImportError:  # pragma: no cover
    C = {
        "green": "#006400", "green_mid": "#004d00", "amber": "#8b6914",
        "red": "#cc0000", "grey": "#606060", "bg": "#f5f5f0",
        "btn_bg": "#d4d0c8",
    }

# $0000 catches the common "JMP [$0000]" NOP-sled idiom used as an
# old-fashioned HALT substitute, so Run stops there instead of
# free-running through it forever -- same default as the Qt build.
DEFAULT_BREAKPOINTS = {0x0000}

WALK_PAGE_SIZE = 256
WALK_INTERVAL_MS = 400


class MemoryWalker(tk.Frame):
    def __init__(self, parent, cpu, on_step_executed=None, on_bp_hit=None, **kwargs):
        super().__init__(parent, bg="#c0c0c0", **kwargs)
        self.cpu = cpu
        self._base = 0
        self._breakpoints = set(DEFAULT_BREAKPOINTS)
        self._user_nav = False
        self._walking = False
        self._walk_after_id = None
        self._on_step_executed = on_step_executed
        self._on_bp_hit = on_bp_hit
        self._build()

    # ---------------------------------------------------------------- build --

    def _build(self):
        # Buttons get both a +3pt font bump (12->15) and ~50% bigger
        # click targets via explicit internal padding -- tk.Button with
        # no padx/pady set defaults to ~1px of internal padding (text-
        # hugging), so BTN_PADX/BTN_PADY below are what actually make
        # them visibly bigger, not just the font.
        BTN_FONT = ("Arial", 15, "bold")
        BTN_PADX, BTN_PADY = 12, 7
        # RUN to BP used to stand out with red text on a different
        # background than the other four buttons -- all five now share
        # one consistent grey, same as the rest of the app's plain
        # buttons (Calculator's control row, etc.), rather than one
        # button looking like a distinct color-coded control.
        BTN_BG = "#d4d0c8"

        nav = tk.Frame(self, bg="#c0c0c0")
        nav.pack(fill="x", padx=8, pady=(8, 2))

        tk.Label(nav, text="Address:", bg="#c0c0c0", font=("Arial", 15)).pack(side="left")
        self.addr_var = tk.StringVar(value="0000")
        addr_entry = tk.Entry(
            nav, textvariable=self.addr_var, width=8,
            font=("Courier New", 18, "bold"),
        )
        addr_entry.pack(side="left", padx=4)
        addr_entry.bind("<Return>", lambda e: self._go())

        tk.Button(
            nav, text="GO", font=BTN_FONT, width=5, bg=BTN_BG,
            padx=BTN_PADX, pady=BTN_PADY,
            command=self._go,
        ).pack(side="left", padx=2)

        nav2 = tk.Frame(self, bg="#c0c0c0")
        nav2.pack(fill="x", padx=8, pady=2)

        # Equal gap after every button (was inconsistent -- "Go to PC"
        # and "RUN to BP" nearly touched while "Clear BPs"/"Walk 64K"
        # had a visible gap -- now all four use the same BTN_GAP).
        BTN_GAP = 8

        tk.Button(
            nav2, text="Go to PC", font=BTN_FONT, bg=BTN_BG,
            padx=BTN_PADX, pady=BTN_PADY,
            command=self._goto_pc,
        ).pack(side="left", padx=(0, BTN_GAP))
        self.run_bp_btn = tk.Button(
            nav2, text="RUN to BP", font=BTN_FONT, bg=BTN_BG,
            padx=BTN_PADX, pady=BTN_PADY,
            command=self.run_to_breakpoint,
        )
        self.run_bp_btn.pack(side="left", padx=(0, BTN_GAP))
        tk.Button(
            nav2, text="Clear BPs", font=BTN_FONT, bg=BTN_BG,
            padx=BTN_PADX, pady=BTN_PADY,
            command=self._clear_all_breakpoints,
        ).pack(side="left", padx=(0, BTN_GAP))
        self.walk_btn = tk.Button(
            nav2, text="Walk 64K", font=BTN_FONT, bg=BTN_BG,
            padx=BTN_PADX, pady=BTN_PADY,
            command=self._toggle_walk,
        )
        self.walk_btn.pack(side="left", padx=(0, BTN_GAP))

        # The static instructional sentence this used to open with
        # ("Click STEP column...") was also the single widest row in
        # the whole panel, forcing the window wider than the actual
        # controls needed -- removed. The label stays (real-time
        # feedback like "BP set at $xxxx" / step results is still
        # useful), it just starts blank instead of pre-loaded with
        # help text.
        self.status_lbl = tk.Label(
            self, text="",
            fg=C["grey"], bg="#c0c0c0", font=("Arial", 14, "italic"), anchor="w",
        )
        self.status_lbl.pack(fill="x", padx=8, pady=(2, 4))

        self.grid = MemoryGrid(
            self,
            get_byte=lambda addr: self.cpu.ram[addr],
            get_touched=lambda addr: bool(self.cpu.ram_touched[addr]),
            get_pc=lambda: self.cpu.pc,
            get_base=lambda: self._base,
            is_bp=lambda addr: addr in self._breakpoints,
            on_toggle_bp=self._toggle_bp,
            on_step=self._do_step,
            visible_rows=18,
        )
        self.grid.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # --------------------------------------------------------- navigation --

    def _go(self):
        try:
            addr = int(self.addr_var.get().strip(), 16) & 0xFFFF
        except ValueError:
            return
        self._stop_walk()
        self._base = addr
        self._user_nav = True
        self.grid.refresh()

    def _goto_pc(self):
        self._stop_walk()
        self._user_nav = False
        self.highlight_pc(self.cpu.pc)
        self._set_status(f"Jumped to PC=${self.cpu.pc:04X}", C["amber"])

    # ------------------------------------------------------- walk 64K ----

    def _toggle_walk(self):
        if self._walking:
            self._stop_walk()
        else:
            self._start_walk()

    def _start_walk(self):
        self._walking = True
        self._user_nav = True
        self.walk_btn.configure(text="Stop Walk", relief="sunken")
        self._set_status("Walking 64K memory space...", C["amber"])
        self._walk_step()

    def _stop_walk(self):
        if self._walking:
            if self._walk_after_id is not None:
                self.after_cancel(self._walk_after_id)
                self._walk_after_id = None
            self._walking = False
            self.walk_btn.configure(text="Walk 64K", relief="raised")
            self._set_status(f"Walk stopped at ${self._base:04X}", C["grey"])

    def _walk_step(self):
        self._base = (self._base + WALK_PAGE_SIZE) % 0x10000
        self.addr_var.set(f"{self._base:04X}")
        self.grid.refresh()
        if self._walking:
            self._walk_after_id = self.after(WALK_INTERVAL_MS, self._walk_step)

    # ---------------------------------------------------------- clicking --
    # (routed through MemoryGrid's on_toggle_bp/on_step callbacks)

    def _toggle_bp(self, addr):
        if addr in self._breakpoints:
            self._breakpoints.discard(addr)
            self._set_status(f"BP removed at ${addr:04X}", C["grey"])
        else:
            self._breakpoints.add(addr)
            self._set_status(f"BP set at ${addr:04X}", C["red"])
        self.grid.refresh()

    def _clear_all_breakpoints(self):
        self._breakpoints.clear()
        self._set_status("All breakpoints cleared.", C["grey"])
        self.grid.refresh()

    # --------------------------------------------------------- single step --

    def _do_step(self):
        if self.cpu.halted:
            self._set_status("CPU is HALTed — Reset before stepping.", C["red"])
            return

        self._stop_walk()
        self._user_nav = False
        mnemonic = self.cpu.step()
        self.highlight_pc(self.cpu.pc)

        if self.cpu.halted:
            self._set_status(f"HALT executed — PC=${self.cpu.pc:04X}", C["red"])
        else:
            self._set_status(
                f"Stepped  PC=${self.cpu.pc:04X}  {mnemonic}  ACC=${self.cpu.acc:02X}",
                C["amber"],
            )

        if self._on_step_executed is not None:
            self._on_step_executed(mnemonic)

    # ------------------------------------------------------- run to BP ----

    def run_to_breakpoint(self):
        if not self._breakpoints:
            self._set_status("No breakpoints set — click a BP cell first.", C["red"])
            return
        if self.cpu.halted:
            self._set_status("CPU is HALTed — Reset before running.", C["red"])
            return

        self._stop_walk()
        self._set_status("Running...", C["grey"])
        self.update_idletasks()

        batch = 500
        executed = 0

        while executed < RUN_LIMIT:
            for _ in range(batch):
                if self.cpu.halted:
                    break
                self.cpu.step()
                executed += 1
                if self.cpu.pc in self._breakpoints:
                    reason = f"BP hit at ${self.cpu.pc:04X} after {executed} steps"
                    self._set_status(reason, C["red"])
                    self.highlight_pc(self.cpu.pc)
                    if self._on_bp_hit is not None:
                        self._on_bp_hit(reason)
                    return

            if self.cpu.halted:
                reason = f"HALT at ${self.cpu.pc:04X} after {executed} steps"
                self._set_status(reason, C["red"])
                self.highlight_pc(self.cpu.pc)
                if self._on_bp_hit is not None:
                    self._on_bp_hit(reason)
                return

            self.update_idletasks()

        reason = f"Step limit ({RUN_LIMIT:,}) reached at ${self.cpu.pc:04X}"
        self._set_status(reason, C["red"])
        self.highlight_pc(self.cpu.pc)
        if self._on_bp_hit is not None:
            self._on_bp_hit(reason)

    # --------------------------------------------------------- PC tracking --

    def highlight_pc(self, pc):
        """Move the ▶ step marker to the row matching the new PC.

        If the user has manually navigated with GO/Walk (_user_nav=True)
        the view is NOT re-anchored -- their chosen address is respected
        even if PC is off-screen. The flag clears once the user steps
        from inside Memory Walker (_do_step), resuming normal
        PC-following.
        """
        pc &= 0xFFFF
        offset = (pc - self._base) & 0xFFFF
        VISIBLE_ROWS = 256  # matches the grid's fixed 256-row backing content

        if offset >= VISIBLE_ROWS:
            if self._user_nav:
                self.grid.refresh()
                return
            LEAD_IN = 4
            self._base = (pc - LEAD_IN) & 0xFFFF
            self.addr_var.set(f"{self._base:04X}")
            offset = LEAD_IN

        self.grid.refresh()
        self.grid.scroll_to_offset(offset)

    def refresh(self):
        """Public refresh -- called by main_window after any CPU step/run
        tick that didn't go through this panel's own controls."""
        self.grid.refresh()

    # ---------------------------------------------------------------- util --

    def _set_status(self, text, colour):
        self.status_lbl.configure(text=text, fg=colour)
