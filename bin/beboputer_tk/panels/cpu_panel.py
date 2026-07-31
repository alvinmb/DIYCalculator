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

"""CPU register display panel -- tkinter port of
beboputer_v7/panels/cpu_panel.py (+ the two LCD-style widgets it uses
from beboputer_v7/widgets/leds.py, LEDDisplay and FlagLight, ported
here as small tk.Label subclasses since they're only used by this one
panel and don't warrant a separate widgets package yet).

Layout (matches the Qt panel / original DIY Calculator screenshot):

    +------------------+  +------------------+
    | Accumulator      |  | Program Counter  |
    +------------------+  +------------------+
    | Instruction Reg  |  | Index Reg        |
    +------------------+  +------------------+
    | Interrupt Vector |  | Stack Pointer    |
    +------------------+  +------------------+

    Status Reg:  I   O   N   Z   C

The "O" flag is the CPU's overflow flag (FLAG_V) -- DIY Calculator
labels it "O" on-screen; internally it's still called V.
"""

from __future__ import annotations

import tkinter as tk

try:
    from beboputer_v7.constants import FLAG_C, FLAG_Z, FLAG_N, FLAG_V, FLAG_I
except ImportError:  # pragma: no cover
    FLAG_C, FLAG_Z, FLAG_N, FLAG_V, FLAG_I = 1, 2, 4, 8, 16

try:
    from beboputer_v7.styles import C
except ImportError:  # pragma: no cover
    C = {
        "blue": "#000080", "lcd_bg": "#c8f0c8", "lcd_fg": "#000000",
        "btn_bdr": "#888888", "red": "#cc0000", "grey": "#606060",
    }


class LEDDisplay(tk.Label):
    """LCD-style hex value readout."""

    def __init__(self, parent, width=3, box_width=None, **kwargs):
        self._width = width
        self._box_width = box_width if box_width is not None else width
        super().__init__(
            parent, bg=C["lcd_bg"], fg="#000000",
            font=("Courier New", 14, "bold"),
            relief="sunken", bd=2, anchor="e",
            width=self._box_width, **kwargs,
        )
        self.set_value(0)

    def set_value(self, val):
        if self._width <= 4:
            self.configure(text=f"${val:0{self._width}X}")
        else:
            self.configure(text=f"{val:08b}")


class FlagLight(tk.Label):
    """LCD-style status-flag indicator: 'x' (unknown) / '0' / '1'."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent, bg=C["lcd_bg"], font=("Courier New", 14, "bold"),
            relief="sunken", bd=2, width=2, anchor="center", **kwargs,
        )
        self.set_unknown()

    def set_on(self, on):
        if on:
            self.configure(text="1", fg=C["red"])
        else:
            self.configure(text="0", fg=C.get("lcd_fg", "#000000"))

    def set_unknown(self):
        self.configure(text="x", fg=C["grey"], font=("Courier New", 14, "bold italic"))


class CPUPanel(tk.Frame):
    _BOX_WIDTH = 6  # shared box width so all 6 registers line up

    def __init__(self, parent, cpu, **kwargs):
        super().__init__(parent, bg="#c0c0c0", **kwargs)
        self.cpu = cpu
        self.flags: dict[str, FlagLight] = {}
        self._build()
        self.refresh()

    # ---------------------------------------------------------------- build --

    def _build(self):
        outer = tk.Frame(self, bg="#c0c0c0")
        outer.pack(fill="both", expand=True, padx=10, pady=8)

        grid = tk.Frame(outer, bg="#c0c0c0")
        grid.pack(fill="x", pady=(0, 8))

        self.acc_disp   = self._reg_field(grid, "Accumulator", 2,     0, 0)
        self.pc_disp    = self._reg_field(grid, "Program Counter", 4, 0, 1)
        self.instr_disp = self._reg_field(grid, "Instruction Reg", 2, 1, 0)
        self.ix_disp    = self._reg_field(grid, "Index Reg", 4,       1, 1)
        self.iv_disp    = self._reg_field(grid, "Interrupt Vector", 4, 2, 0)
        self.sp_disp    = self._reg_field(grid, "Stack Pointer", 4,   2, 1)

        flag_box = tk.LabelFrame(
            outer, text="Status Reg", bg="#c0c0c0",
            font=("Arial", 9, "bold"), labelanchor="n",
            padx=12, pady=8,
        )
        flag_box.pack(fill="x")

        flag_row = tk.Frame(flag_box, bg="#c0c0c0")
        flag_row.pack()

        flag_order = [("I", "I"), ("O", "V"), ("N", "N"), ("Z", "Z"), ("C", "C")]
        for disp_name, cpu_key in flag_order:
            self._flag_field(flag_row, disp_name, cpu_key)

    def _reg_field(self, parent, label, width, row, col):
        cell = tk.Frame(parent, bg="#c0c0c0")
        cell.grid(row=row, column=col, padx=6, pady=3, sticky="n")
        tk.Label(
            cell, text=label, fg=C["blue"], bg="#c0c0c0",
            font=("Arial", 9, "bold"),
        ).pack()
        disp = LEDDisplay(cell, width=width, box_width=self._BOX_WIDTH)
        disp.pack()
        return disp

    def _flag_field(self, parent, disp_name, cpu_key):
        cell = tk.Frame(parent, bg="#c0c0c0")
        cell.pack(side="left", padx=4)
        tk.Label(
            cell, text=disp_name, fg=C["blue"], bg="#c0c0c0",
            font=("Arial", 9, "bold"),
        ).pack()
        fl = FlagLight(cell)
        fl.pack()
        self.flags[cpu_key] = fl

    # ---------------------------------------------------------------- refresh

    def refresh(self):
        self.acc_disp.set_value(self.cpu.acc)
        self.pc_disp.set_value(self.cpu.pc)
        self.sp_disp.set_value(self.cpu.sp)
        self.ix_disp.set_value(self.cpu.ix)
        self.instr_disp.set_value(self.cpu.instr)
        self.iv_disp.set_value(getattr(self.cpu, "_intr_vector", 0xFFFE))

        f = self.cpu.flags
        t = getattr(self.cpu, "flags_touched", 0xFF)
        for cpu_key, mask in (
            ("I", FLAG_I), ("V", FLAG_V), ("N", FLAG_N),
            ("Z", FLAG_Z), ("C", FLAG_C),
        ):
            if t & mask:
                self.flags[cpu_key].set_on(f & mask)
            else:
                self.flags[cpu_key].set_unknown()
