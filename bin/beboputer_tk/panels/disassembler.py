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

"""Disassembler panel -- shows decoded instructions starting at a chosen
address. tkinter port of beboputer_v7/panels/disassembler.py.

cpu.disassemble_at() (in beboputer_v7/cpu.py) does all the real work and
has zero Qt dependency, so it's reused completely unchanged -- this
panel is just a thin From/Disassemble text-output wrapper around it,
same as the Qt version.
"""

from __future__ import annotations

import tkinter as tk


class DisassemblerPanel(tk.Frame):
    def __init__(self, parent, cpu, **kwargs):
        super().__init__(parent, bg="#c0c0c0", **kwargs)
        self.cpu = cpu
        self._build()

    def _build(self):
        nav = tk.Frame(self, bg="#c0c0c0")
        nav.pack(fill="x", padx=8, pady=(8, 4))

        tk.Label(nav, text="From:", bg="#c0c0c0", font=("Arial", 12)).pack(side="left")
        self.addr_var = tk.StringVar(value="0000")
        addr_entry = tk.Entry(
            nav, textvariable=self.addr_var, width=8,
            font=("Courier New", 18, "bold"),
        )
        addr_entry.pack(side="left", padx=4)
        addr_entry.bind("<Return>", lambda e: self._disassemble())

        tk.Button(
            nav, text="Disassemble", font=("Arial", 12, "bold"),
            command=self._disassemble,
        ).pack(side="left", padx=2)

        self.output = tk.Text(
            self, font=("Courier New", 20), bg="#ffffff",
            state="disabled", wrap="none",
        )
        self.output.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._disassemble()

    def _disassemble(self):
        try:
            addr = int(self.addr_var.get(), 16)
        except ValueError:
            addr = 0
        lines = self.cpu.disassemble_at(addr, 32)
        text = ""
        for (pc, op, mnem, operand) in lines:
            text += f"  ${pc:04X}:  {op:02X}  {mnem:<6} {operand}\n"
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")

    def refresh_at_pc(self, pc):
        self.addr_var.set(f"{pc:04X}")
        self._disassemble()
