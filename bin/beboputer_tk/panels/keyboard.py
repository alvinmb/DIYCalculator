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

"""On-screen Keyboard -- sends ASCII bytes to port $F011. tkinter port
of beboputer_v7/tools/keyboard.py.

Layout matches the Qt version's screenshot-derived rows (ESC row,
number row, QWERTY, ASDF, ZXCV, bottom row). The HEX display (top
row) shows $XX for the last key pressed. CAPS and SHIFT toggle letter
capitalisation. Arrow keys send control codes 0x1C-0x1F equivalents
(Le/Ri/Up/Do, matching the Qt key map exactly).
"""

from __future__ import annotations

import tkinter as tk

_PORT = 0xF011


def _k(lbl, val, m=1.0):
    return (lbl, val, m)


def _rows():
    return [
        [_k("ESC", 27, 1.2),
         _k("!", 33), _k("@", 64), _k("#", 35), _k("$", 36),
         _k("%", 37), _k("^", 94), _k("Amp", 38), _k("*", 42),
         _k("(", 40), _k(")", 41), _k("_", 95), _k("+", 43),
         None,  # hex display slot
         _k('"', 34)],

        [_k("~", 126),
         _k("1", 49), _k("2", 50), _k("3", 51), _k("4", 52),
         _k("5", 53), _k("6", 54), _k("7", 55), _k("8", 56),
         _k("9", 57), _k("0", 48), _k("-", 45), _k("=", 61),
         _k("BSpace", 0x04, 1.5),
         _k("<", 60)],

        [_k("TAB", 9, 1.4),
         _k("Q", ord("Q")), _k("W", ord("W")), _k("E", ord("E")),
         _k("R", ord("R")), _k("T", ord("T")), _k("Y", ord("Y")),
         _k("U", ord("U")), _k("I", ord("I")), _k("O", ord("O")),
         _k("P", ord("P")),
         _k("[", 91), _k("]", 93), _k("\\", 92),
         _k(">", 62)],

        [("CAPS", None, 1.55),
         _k("A", ord("A")), _k("S", ord("S")), _k("D", ord("D")),
         _k("F", ord("F")), _k("G", ord("G")), _k("H", ord("H")),
         _k("J", ord("J")), _k("K", ord("K")), _k("L", ord("L")),
         _k(":", 58), _k("'", 39),
         _k("ENTER", 0x05, 1.55),
         _k("?", 63)],

        [("SHIFT", None, 2.0),
         _k("Z", ord("Z")), _k("X", ord("X")), _k("C", ord("C")),
         _k("V", ord("V")), _k("B", ord("B")), _k("N", ord("N")),
         _k("M", ord("M")),
         _k(".", 46), _k(".", 46), _k("/", 47),
         _k("Le", 0x0A), _k("Ri", 0x09),
         _k(";", 59)],

        [("CTRL", None, 1.6), ("ALT", None, 1.6),
         _k("SPACE", 32, 5.3),
         _k("Up", 0x07), _k("Do", 0x08),
         _k("|", 124)],
    ]


class KeyboardPanel(tk.Frame):
    """On-screen keyboard. Each key press writes one ASCII byte to $F011."""

    def __init__(self, parent, cpu, terminal_cb=None, **kwargs):
        super().__init__(parent, bg="#c0c0c0", **kwargs)
        self.cpu = cpu
        self._terminal_cb = terminal_cb
        self._caps = False
        self._shift = False
        self._build()

    def _build(self):
        root = tk.Frame(self, bg="#c0c0c0")
        root.pack(padx=6, pady=6)

        self._hex = tk.Label(
            root, text="$--", bg="#000000", fg="#ffffff",
            font=("Courier New", 16, "bold"), relief="sunken", bd=2, width=5,
        )

        for r, row in enumerate(_rows()):
            hbox = tk.Frame(root, bg="#c0c0c0")
            hbox.grid(row=r, column=0, sticky="w", pady=1)
            for item in row:
                if item is None:
                    self._hex.pack(side="left", padx=1, in_=hbox)
                else:
                    label, val, mult = item
                    self._make_btn(hbox, label, val, mult).pack(side="left", padx=1)

    def _make_btn(self, parent, label, val, mult):
        w = max(2, int(4 * mult))
        fg = "#000000"
        btn = tk.Button(
            parent, text=label, width=w, font=("Arial", 11, "bold"), fg=fg,
            relief="raised", bd=1,
        )
        if label in ("CAPS", "SHIFT"):
            btn._active = False

            def _toggle(lbl=label, b=btn):
                b._active = not b._active
                b.configure(relief="sunken" if b._active else "raised",
                            bg="#cc0000" if b._active else "SystemButtonFace",
                            fg="#ffffff" if b._active else "#000000")
                self._mod(lbl, b._active)
            btn.configure(command=_toggle)
        elif val is not None:
            btn.configure(command=lambda v=val, lbl=label: self._press(v, lbl))
        # CTRL / ALT -- cosmetic only, no command
        return btn

    def _mod(self, label, on):
        if label == "CAPS":
            self._caps = on
        else:
            self._shift = on

    def _press(self, val, label):
        if len(label) == 1 and label.isalpha():
            val = ord(label.upper() if (self._caps or self._shift) else label.lower())
        val &= 0xFF
        self.cpu._write(_PORT, val)
        self._hex.configure(text=f"${val:02X}")
        if self._terminal_cb is not None:
            self._terminal_cb(val)
