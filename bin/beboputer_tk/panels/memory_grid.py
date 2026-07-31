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

"""memory_grid.py -- the 256-row BP/STEP/ADDRESS/DATA table widget at the
heart of Memory Walker.

Promoted from prototypes/tkinter_migration/memory_grid.py (Phase 0 spike,
verified at ~9.3ms/refresh for a full 256-row redraw -- comfortably fast
enough for single-stepping and Run's refresh cadence). Two changes from
the spike version:

  - Breakpoints and the view's base address are no longer owned by this
    widget (the spike's toggle_bp_local()/self.base were a demo
    convenience). They're owned by MemoryWalker instead, matching the Qt
    panel's self._breakpoints/self._base -- so main_window.py can inspect
    mem_walker._breakpoints directly for Run's breakpoint check, the same
    way beboputer_v7.main_window._run_tick() does. This widget just reads
    them through get_base()/is_bp() callables.
  - Added scroll_to_offset(), matching Qt's QTableWidget.scrollToItem()
    call in highlight_pc() -- keeps the ▶ PC marker in view as it moves.

Rendering approach (why not ttk.Treeview or 1,024 individual Label
widgets -- see the spike's original docstring for the full reasoning):
one monospaced tk.Text widget, the whole grid as plain text, per-
substring color tags at fixed character-column offsets so a click's
(row, col) is recovered directly from the Text index tkinter already
provides.
"""

from __future__ import annotations

import tkinter as tk

try:
    from beboputer_v7.styles import C
except ImportError:  # pragma: no cover
    C = {
        "green": "#006400", "green_mid": "#004d00", "amber": "#8b6914",
        "red": "#cc0000", "grey": "#606060", "bg": "#f5f5f0",
    }

ROWS = 256
COL_BP_W, COL_STEP_W, COL_ADDR_W, COL_DATA_W = 4, 4, 8, 6
BP_START, BP_END = 0, COL_BP_W
STEP_START, STEP_END = BP_END, BP_END + COL_STEP_W
ADDR_START, ADDR_END = STEP_END, STEP_END + COL_ADDR_W
DATA_START, DATA_END = ADDR_END, ADDR_END + COL_DATA_W


class MemoryGrid(tk.Frame):
    """Scrollable 256-row memory dump: BP | STEP | ADDRESS | DATA.

    Parameters
    ----------
    get_byte(addr) -> int
    get_touched(addr) -> bool
        Undefined (never-written) RAM shows "XX", matching real hardware
        where power-on RAM contents are indeterminate.
    get_pc() -> int
    get_base() -> int
        Absolute RAM address shown in row 0.
    is_bp(addr) -> bool
    on_toggle_bp(addr), on_step()
        Called when the user clicks the BP or STEP column.
    """

    def __init__(self, parent, get_byte, get_touched, get_pc, get_base,
                 is_bp, on_toggle_bp, on_step, visible_rows=20, **kwargs):
        super().__init__(parent, **kwargs)
        self.get_byte = get_byte
        self.get_touched = get_touched
        self.get_pc = get_pc
        self.get_base = get_base
        self.is_bp = is_bp
        self.on_toggle_bp = on_toggle_bp
        self.on_step = on_step

        header = tk.Label(
            self, text=f"{'BP':<{COL_BP_W}}{'ST':<{COL_STEP_W}}"
                       f"{'ADDR':<{COL_ADDR_W}}{'DATA':<{COL_DATA_W}}",
            font=("Courier New", 14, "bold"), anchor="w", bg="#dcdcdc",
        )
        header.pack(fill="x")

        text_frame = tk.Frame(self)
        text_frame.pack(fill="both", expand=True)

        self.text = tk.Text(
            text_frame, font=("Courier New", 14), width=22, height=visible_rows,
            bg=C.get("bg", "#f5f5f0"), cursor="arrow", wrap="none", state="disabled",
            highlightthickness=0, bd=1, relief="sunken",
        )
        vsb = tk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=vsb.set)
        self.text.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        for name, color in (
            ("addr_normal", C["green_mid"]), ("addr_pc", C["green"]),
            ("data_normal", "#000000"), ("data_undefined", C["grey"]),
            ("data_pc", C["amber"]),
            ("bp_set", C["red"]), ("step_pc", C["amber"]), ("step_idle", C["grey"]),
        ):
            self.text.tag_configure(name, foreground=color)

        self.text.tag_configure("row_pc_bg", background="#fff2cc")

        self.text.bind("<Button-1>", self._on_click)

        self.refresh()

    # -- rendering ------------------------------------------------------------

    def refresh(self):
        base = self.get_base()
        pc = self.get_pc()

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")

        for row in range(ROWS):
            addr = (base + row) & 0xFFFF
            is_pc = addr == pc
            touched = self.get_touched(addr)
            b = self.get_byte(addr)

            bp_char = "●" if self.is_bp(addr) else " "
            step_char = "▶" if is_pc else "·"
            addr_str = f"${addr:04X}"
            data_str = f"{b:02X}" if touched else "XX"

            line = (f"{bp_char:<{COL_BP_W}}{step_char:<{COL_STEP_W}}"
                    f"{addr_str:<{COL_ADDR_W}}{data_str:<{COL_DATA_W}}\n")
            line_start = f"{row + 1}.0"
            self.text.insert("end", line)

            def span(col_start, col_end, row=row):
                return (f"{row + 1}.{col_start}", f"{row + 1}.{col_end}")

            if self.is_bp(addr):
                s, e = span(BP_START, BP_END)
                self.text.tag_add("bp_set", s, e)

            s, e = span(STEP_START, STEP_END)
            self.text.tag_add("step_pc" if is_pc else "step_idle", s, e)

            s, e = span(ADDR_START, ADDR_END)
            self.text.tag_add("addr_pc" if is_pc else "addr_normal", s, e)

            s, e = span(DATA_START, DATA_END)
            if is_pc:
                self.text.tag_add("data_pc", s, e)
            elif not touched:
                self.text.tag_add("data_undefined", s, e)
            else:
                self.text.tag_add("data_normal", s, e)

            if is_pc:
                self.text.tag_add("row_pc_bg", line_start, f"{row + 1}.end")

        self.text.configure(state="disabled")

    def scroll_to_offset(self, offset):
        """Scroll so row *offset* is visible -- mirrors Qt's
        table.scrollToItem() call in MemoryWalker.highlight_pc()."""
        self.text.see(f"{offset + 1}.0")

    # -- clicking ---------------------------------------------------------------

    def _on_click(self, event):
        index = self.text.index(f"@{event.x},{event.y}")
        line_str, col_str = index.split(".")
        row = int(line_str) - 1
        col = int(col_str)
        if not (0 <= row < ROWS):
            return "break"
        addr = (self.get_base() + row) & 0xFFFF
        if BP_START <= col < BP_END:
            self.on_toggle_bp(addr)
        elif STEP_START <= col < STEP_END:
            self.on_step()
        return "break"  # swallow the click so Text doesn't move its own cursor
