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

Keys are sized in real pixels (KW/KH/SP below), not tk.Button's
default character-count width -- that matters for two things this
file used to get wrong:
  - "make the keyboard 25% bigger" is a real, precise multiply on the
    px dimensions; the old width=max(2, int(4*mult)) character-count
    scheme rounded so coarsely that e.g. ESC (mult=1.2) and a plain
    key (mult=1.0) came out the exact same rendered width (int(4.8)
    == int(4) == 4), silently losing the width-multiplier distinction
    the row data asked for.
  - the bottom row's Up/Do/| keys are aligned under row 4's Le/Ri/;
    by measuring real, already-built geometry and inserting a spacer
    of the exact remaining gap (see _build()'s row-5 handling) --
    Qt's version does the same alignment with a hardcoded 191px
    spacer, but that number was derived for Qt's own KW/KH pixel
    scale and wouldn't transfer correctly to this port's (different)
    scale, so it's computed here instead of copied.
"""

from __future__ import annotations

import tkinter as tk

_PORT = 0xF011

# Base key pixel dimensions -- 25% bigger than this port's original
# character-width-based sizing (measured: a mult=1.0 key used to
# render at 66x32px with a 2px gap; 66*1.25=82.5, 32*1.25=40,
# 2*1.25=2.5, all rounded to the nearest px below).
KW = 82   # standard key width  (px), before the per-key `mult`
KH = 40   # key height          (px)
SP = 3    # gap between keys    (px)

# Hex "last key sent" display -- sized to match KH (same height as a
# key, as in Qt's version) with a width scaled the same 25% as the
# keys (was 71x32, ~= KW*1.1 at the old scale).
HEX_W = 90
HEX_FONT = ("Courier New", 20, "bold")

BTN_FONT = ("Arial", 17, "bold")


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

        # Row 5 -- CTRL/ALT/SPACE, then Up/Do/| (the alignment spacer
        # between SPACE and Up is computed at build time, not stored
        # here -- see _build()).
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
        self._le_x = None  # row 4's "Le" key's left-edge x -- row 5's spacer aligns to it
        self._build()

    def _build(self):
        root = tk.Frame(self, bg="#c0c0c0")
        root.pack(padx=6, pady=6)

        rows = _rows()

        # Rows 0-4 build normally. Le's left-edge x is captured via
        # winfo_reqwidth() -- NOT winfo_x()/winfo_rootx(), which only
        # reflect real assigned coordinates once the widget tree is
        # actually mapped to an on-screen window. _build() runs from
        # __init__(), before the caller has packed/placed this panel
        # anywhere, so nothing here is mapped yet and winfo_x() would
        # read back 0 for everything -- reqwidth (the geometry manager's
        # *requested* size) is available regardless of mapping, so
        # summing it as each item is packed gives an accurate x-offset
        # even at construction time.
        for r in range(5):
            hbox = tk.Frame(root, bg="#c0c0c0")
            hbox.grid(row=r, column=0, sticky="w", pady=(0, SP))
            for item in rows[r]:
                if item is None:
                    # Hex "last key sent" display -- built directly as a
                    # child of *this* row's frame (not pack(in_=hbox)'d
                    # in from elsewhere -- a widget whose real Tk parent
                    # differs from its packing-geometry parent is a
                    # legitimate but easy-to-get-subtly-wrong construct,
                    # and building it in place removes that risk
                    # entirely). Fixed-pixel-size wrapper, same trick
                    # _make_btn() uses for keys: a plain tk.Label's
                    # width= is character units, not pixels, so it can't
                    # be sized to match KH directly.
                    hex_cell = tk.Frame(hbox, width=HEX_W, height=KH, bg="#c0c0c0")
                    hex_cell.pack_propagate(False)
                    self._hex = tk.Label(
                        hex_cell, text="$--", bg="#000000", fg="#ffffff",
                        font=HEX_FONT, relief="sunken", bd=2,
                    )
                    self._hex.pack(fill="both", expand=True)
                    hex_cell.pack(side="left", padx=(0, SP))
                    continue
                label, val, mult = item
                if label == "Le":
                    hbox.update_idletasks()
                    self._le_x = hbox.winfo_reqwidth()
                cell = self._make_btn(hbox, label, val, mult)
                cell.pack(side="left", padx=(0, SP))

        # Row 5 needs row 4's real geometry before its last three keys
        # (Up/Do/|) can be positioned -- build CTRL/ALT/SPACE first,
        # measure how far along the row that leaves us against Le's
        # captured x (not a hardcoded pixel guess, see module
        # docstring), then insert a spacer of exactly the remaining gap
        # before continuing with Up/Do/|.
        ctrl, alt, space, up, do, pipe = rows[5]
        hbox5 = tk.Frame(root, bg="#c0c0c0")
        hbox5.grid(row=5, column=0, sticky="w", pady=(0, SP))
        for label, val, mult in (ctrl, alt, space):
            self._make_btn(hbox5, label, val, mult).pack(side="left", padx=(0, SP))

        hbox5.update_idletasks()
        next_x = hbox5.winfo_reqwidth()
        le_x = self._le_x if self._le_x is not None else next_x
        spacer_w = max(0, le_x - next_x)
        if spacer_w > 0:
            tk.Frame(hbox5, width=spacer_w, height=1, bg="#c0c0c0").pack(side="left")

        for label, val, mult in (up, do, pipe):
            self._make_btn(hbox5, label, val, mult).pack(side="left", padx=(0, SP))

    def _make_btn(self, parent, label, val, mult):
        # Fixed-pixel-width wrapper frame (pack_propagate(False)) around
        # the real Button -- tk.Button's own width= option is measured
        # in characters, which rounds so coarsely at these mult values
        # that nearby multipliers (e.g. 1.2 vs 1.0) can render
        # identically (see module docstring). Wrapping in a frame with
        # an explicit pixel width sidesteps that entirely.
        w = max(24, int(KW * mult))
        cell = tk.Frame(parent, width=w, height=KH, bg="#c0c0c0")
        cell.pack_propagate(False)
        fg = "#000000"
        btn = tk.Button(
            cell, text=label, font=BTN_FONT, fg=fg,
            relief="raised", bd=1,
        )
        btn.pack(fill="both", expand=True)
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
        return cell

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
