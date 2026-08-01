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

"""RUN / STEP / HALT / RESET buttons, address/data bus readout, switches.

tkinter port of beboputer_v7/panels/control_panel.py. Qt's pyqtSignal
becomes plain callback parameters (on_run/on_step/on_halt/on_reset),
since tkinter buttons just take command= directly -- no signal/slot
layer needed for a single-widget-to-single-handler wire-up like this.
"""

from __future__ import annotations

import tkinter as tk

from .workbench import ToggleSwitch

try:
    from beboputer_v7.styles import C
except ImportError:  # pragma: no cover
    C = {
        "blue": "#000080", "green": "#006400", "amber": "#8b6914",
        "red": "#cc0000", "btn_bg": "#d4d0c8", "btn_bdr": "#888888",
    }


class ControlPanel(tk.Frame):
    def __init__(self, parent, on_run=None, on_step=None,
                 on_halt=None, on_reset=None, **kwargs):
        super().__init__(parent, bg="#c0c0c0", **kwargs)
        self.on_run = on_run
        self.on_step = on_step
        self.on_halt = on_halt
        self.on_reset = on_reset
        self.switches: list[ToggleSwitch] = []
        self._build()

    def _build(self):
        layout = tk.Frame(self, bg="#c0c0c0")
        layout.pack(fill="both", expand=True, padx=8, pady=8)

        tk.Label(
            layout, text="◈ CONTROL PANEL", fg=C["blue"], bg="#c0c0c0",
            font=("Arial", 14, "bold"),
        ).pack(anchor="w", pady=(0, 6))

        btn_row = tk.Frame(layout, bg="#c0c0c0")
        btn_row.pack(fill="x", pady=(0, 6))
        self.run_btn   = self._btn(btn_row, "▶  RUN",   C["green"], self.on_run)
        self.step_btn  = self._btn(btn_row, "⏭  STEP",  C["amber"], self.on_step)
        self.halt_btn  = self._btn(btn_row, "⏸  HALT",  C["red"],   self.on_halt)
        self.reset_btn = self._btn(btn_row, "↺  RESET", C["blue"],  self.on_reset)
        for b in (self.run_btn, self.step_btn, self.halt_btn, self.reset_btn):
            b.pack(side="left", padx=3)

        bus_box = tk.LabelFrame(
            layout, text="Address / Data Bus", bg="#c0c0c0",
            font=("Arial", 12, "bold"), padx=6, pady=6,
        )
        bus_box.pack(fill="x", pady=(0, 6))
        tk.Label(bus_box, text="Address Bus:", bg="#c0c0c0").grid(row=0, column=0, sticky="w")
        self.addr_disp = tk.Entry(bus_box, justify="left", state="readonly", width=10)
        self._set_readonly(self.addr_disp, "$0000")
        self.addr_disp.grid(row=0, column=1, sticky="w", padx=6)
        tk.Label(bus_box, text="Data Bus:", bg="#c0c0c0").grid(row=1, column=0, sticky="w")
        self.data_disp = tk.Entry(
            bus_box, justify="left", state="readonly", width=6,
            font=("Courier New", 15),
        )
        self._set_readonly(self.data_disp, "$00")
        self.data_disp.grid(row=1, column=1, sticky="w", padx=6, pady=(2, 0))

        # Same lever-style ToggleSwitch used by Workbench's SwitchBank,
        # replacing the plain square tk.Checkbutton boxes this used to
        # have -- visually consistent with the other switch-input panel
        # in the app instead of looking like an unrelated widget style.
        sw_box = tk.LabelFrame(
            layout, text="Data Switches  (manual input)", bg="#c0c0c0",
            font=("Arial", 12, "bold"), padx=6, pady=6,
        )
        sw_box.pack(fill="x", pady=(0, 6))
        self.switches = []
        for i in range(7, -1, -1):
            col = 7 - i
            cell = tk.Frame(sw_box, bg="#c0c0c0")
            cell.grid(row=0, column=col, padx=3)
            tk.Label(cell, text=str(i), bg="#c0c0c0", font=("Arial", 10)).pack()
            sw = ToggleSwitch(cell)
            sw.pack()
            self.switches.insert(0, sw)

        enter_row = tk.Frame(layout, bg="#c0c0c0")
        enter_row.pack(fill="x")
        self.enter_btn = tk.Button(
            enter_row, text="ENTER  ↵", fg=C["green"], bg=C["btn_bg"],
            relief="raised", bd=1, font=("Arial", 12, "bold"), padx=10, pady=3,
        )
        self.enter_btn.pack(side="right")

    @staticmethod
    def _set_readonly(entry, text):
        entry.config(state="normal")
        entry.delete(0, "end")
        entry.insert(0, text)
        entry.config(state="readonly")

    def _btn(self, parent, text, color, handler):
        b = tk.Button(
            parent, text=text, fg=color, bg=C["btn_bg"], relief="raised",
            bd=1, font=("Arial", 12, "bold"), padx=8, pady=4,
            command=handler if handler is not None else (lambda: None),
        )
        return b

    def get_switch_value(self) -> int:
        val = 0
        for i, sw in enumerate(self.switches):
            if sw.is_on:
                val |= (1 << i)
        return val

    def set_bus(self, addr: int, data: int):
        self._set_readonly(self.addr_disp, f"${addr:04X}")
        self._set_readonly(self.data_disp, f"${data:02X}")
