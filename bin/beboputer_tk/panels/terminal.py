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

"""Terminal -- CRT-style output device driven by memory-mapped port
$F028. tkinter port of beboputer_v7/panels/terminal.py.

This is a Beboputer peripheral, not a diagnostic tool. System/emulator
messages go to Message Display instead.

Screen state follows the calculator's On/Off button:
  - Off -> screen is black (write_char() calls are silently discarded)
  - On  -> screen is white (characters from $F028 writes are rendered)

The CPU write-hook for $F028 is registered in main_window.py, same as
the Qt build -- any STORE ($F028), A instruction routes ACC directly
to write_char(). (beboputer_v7.main_window._check_port_output(), which
forwards cpu.ports_out[1] to the terminal, was traced and found dead --
nothing in cpu.py ever writes ports_out[1]; it's a leftover from an
older port-based I/O model that predates the $F028 memory-mapped hook.
Not ported here, same reasoning as the other dead-code findings this
session.)
"""

from __future__ import annotations

import tkinter as tk


class Terminal(tk.Frame):
    """CRT-style output device driven by port $F028."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#808080", **kwargs)
        self._powered = False
        self._build()

    def _build(self):
        # outer raised "casing" bevel
        casing = tk.Frame(self, bg="#808080", bd=4, relief="raised")
        casing.pack(fill="both", expand=True, padx=4, pady=4)

        # inner sunken "bezel" -- the screen surround
        bezel = tk.Frame(casing, bg="#404040", bd=3, relief="sunken")
        bezel.pack(fill="both", expand=True, padx=8, pady=8)

        self.screen = tk.Text(
            bezel, font=("Courier New", 16), bd=0, highlightthickness=0,
            wrap="word", state="disabled",
        )
        self.screen.pack(fill="both", expand=True, padx=4, pady=4)

        self._apply_power(False)

    # -- power control ------------------------------------------------------

    def _apply_power(self, on: bool):
        self._powered = on
        if on:
            self.screen.configure(bg="#ffffff", fg="#000000")
        else:
            self.screen.configure(bg="#000000", fg="#000000")
            self.clear()

    def set_power(self, on: bool):
        """Called on Calculator power-on/off (Calculator.control("On/Off"))."""
        self._apply_power(on)

    # -- reset ----------------------------------------------------------------

    def clear(self):
        """Wipe the screen buffer -- called on CPU Reset. Does not change
        power state, just blanks whatever was printed."""
        self.screen.configure(state="normal")
        self.screen.delete("1.0", "end")
        self.screen.configure(state="disabled")

    # -- device output ----------------------------------------------------

    def write_char(self, ch: int):
        """Receive one byte from port $F028 and paint it on the screen.

        Printable ASCII (32-126) is rendered directly; 0x0A (\\n) moves
        to the next line. All other values are ignored. Silently
        discarded when the terminal is powered off.
        """
        if not self._powered:
            return
        if 32 <= ch <= 126:
            self.screen.configure(state="normal")
            self.screen.insert("end", chr(ch))
            self.screen.see("end")
            self.screen.configure(state="disabled")
        elif ch == 0x0A:
            self.screen.configure(state="normal")
            self.screen.insert("end", "\n")
            self.screen.see("end")
            self.screen.configure(state="disabled")
