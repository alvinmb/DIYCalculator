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

"""Workbench 1 -- dual 8-bit switch input banks + LED / 7-segment
outputs. tkinter port of beboputer_v7/tools/workbench.py.

Port map (as actually wired by the Qt source's ADDR_* constants --
note the module docstring up there says $F020/$F021/$F022/$F023, but
the real constants used by _install_hooks()/_sw1_write()/_sw2_write()
are $F000/$F001/$F022/$F021/$F023/$F024. That mismatch predates this
port and isn't something introduced here -- the constants below are
copied from the working code, not the stale comment.):

    Input   $F000   8-Bit Switch Bank 1
    Input   $F001   8-Bit Switch Bank 2
    Output  $F022   8-Bit LED Display
    Output  $F021   7-Segment un-decoded (bits 0-6 -> segments a-g)
    Output  $F023   7-Segment decoded (low nibble -> hex digit 0-F)
    Output  $F024   Dual 7-Segment decoded (hi nibble=left, lo=right)

Visual simplification from the Qt version: the Qt build's un-decoded
and decoded 7-segment displays are rendered from photographic BMP
assets (BITMAPS/USEGn.BMP / DSEGn.BMP). tkinter's PhotoImage has no
built-in BMP decoder (only GIF/PGM/PPM/PNG without adding a Pillow
dependency), so all three 7-segment displays here are drawn as vector
polygons on a tk.Canvas instead -- same segment-bit truth table
(_DIGITS), same on/off colors, just line-drawn rather than
photorealistic. The single-digit vector renderer doubles as both the
"un-decoded" and "decoded" display (only the bit-to-segment mapping
differs, controlled by the `decoded` flag), matching the Qt SevenSeg
class Workbench itself doesn't use directly but which this port
adopts as the one real implementation instead of duplicating
image-vs-vector code paths.

Not ported: the switch-click .wav sound (QSound has no tkinter
equivalent -- same already-flagged Sound gap in TKINTER_MIGRATION.md).
"""

from __future__ import annotations

import tkinter as tk

ADDR_SW1 = 0xF000
ADDR_SW2 = 0xF001
ADDR_LED = 0xF022
ADDR_SEG1 = 0xF021
ADDR_SEG2 = 0xF023
ADDR_SEG3 = 0xF024

# bit 0=a(top) 1=b(upper-right) 2=c(lower-right) 3=d(bottom)
# bit 4=e(lower-left) 5=f(upper-left) 6=g(middle)
_DIGITS = [
    0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07,
    0x7F, 0x6F, 0x77, 0x7C, 0x39, 0x5E, 0x79, 0x71,
]


class ToggleSwitch(tk.Canvas):
    """Single toggle switch. Click to flip. Lever up=OFF(red), down=ON(green)."""

    _W, _H = 30, 46

    def __init__(self, parent, on_change=None, **kwargs):
        super().__init__(parent, width=self._W, height=self._H,
                          bg="#c0c0c0", highlightthickness=0, cursor="hand2", **kwargs)
        self._on = False
        self._on_change = on_change
        self.bind("<Button-1>", self._toggle)
        self._draw()

    @property
    def is_on(self) -> bool:
        return self._on

    def set_on(self, on: bool, notify=True):
        if self._on != on:
            self._on = on
            self._draw()
            if notify and self._on_change is not None:
                self._on_change(self._on)

    def _toggle(self, event=None):
        self._on = not self._on
        self._draw()
        if self._on_change is not None:
            self._on_change(self._on)

    def _draw(self):
        self.delete("all")
        W, H = self._W, self._H
        cx = W // 2
        self.create_rectangle(3, H // 2 + 3, W - 3, H - 3,
                               fill="#5a3418", outline="#2a1508")
        lw, lh = 12, H // 2 + 4
        lx = cx - lw // 2
        ly = H // 2 - 4 if self._on else 2
        col = "#00aa00" if self._on else "#cc0000"
        self.create_rectangle(lx, ly, lx + lw, ly + lh, fill=col, outline="#1a1a1a")


class SwitchBank(tk.Frame):
    """Labelled row of 8 toggle switches representing one input byte."""

    def __init__(self, parent, label, on_value_changed=None, **kwargs):
        super().__init__(parent, bg="#c0c0c0", **kwargs)
        self._switches: list[ToggleSwitch] = []
        self._on_value_changed = on_value_changed
        tk.Label(self, text=label, bg="#c0c0c0", font=("Arial", 12, "bold")).pack(anchor="w")
        row = tk.Frame(self, bg="#c0c0c0")
        row.pack()
        for _ in range(8):
            sw = ToggleSwitch(row, on_change=self._changed)
            sw.pack(side="left", padx=3)
            self._switches.append(sw)

    def _changed(self, _on):
        if self._on_value_changed is not None:
            self._on_value_changed(self.value())

    def value(self) -> int:
        v = 0
        for i, sw in enumerate(self._switches):
            if sw.is_on:
                v |= 1 << (7 - i)
        return v

    def reset(self):
        for sw in self._switches:
            sw.set_on(False, notify=False)
        if self._on_value_changed is not None:
            self._on_value_changed(self.value())


class LEDBar(tk.Canvas):
    """Row of 8 green LEDs driven by a byte value."""

    _D, _SP, _X0 = 20, 8, 6

    def __init__(self, parent, **kwargs):
        D, SP, X0 = self._D, self._SP, self._X0
        w = X0 + 8 * D + 7 * SP + X0
        super().__init__(parent, width=w, height=D + 12, bg="#c0c0c0",
                          highlightthickness=0, **kwargs)
        self._value = 0
        self._draw()

    def set_value(self, val: int):
        val &= 0xFF
        if self._value != val:
            self._value = val
            self._draw()

    def _draw(self):
        self.delete("all")
        D, SP, X0 = self._D, self._SP, self._X0
        y0 = 6
        for i in range(8):
            bit = (self._value >> (7 - i)) & 1
            x = X0 + i * (D + SP)
            fill = "#00cc00" if bit else "#1a3a1a"
            self.create_oval(x, y0, x + D, y0 + D, fill=fill, outline="#004400")


class SevenSeg(tk.Canvas):
    """Single vector-drawn 7-segment digit.

    decoded=False -- raw bits 0-6 map directly to segments a-g.
    decoded=True  -- low nibble of value -> 0-F digit shape (_DIGITS).
    """

    _W, _H, _T, _G, _MX, _MY = 50, 80, 7, 3, 7, 6
    _ON, _OFF = "#dd2200", "#2a0600"

    def __init__(self, parent, decoded=True, **kwargs):
        super().__init__(parent, width=self._W, height=self._H,
                          bg="#080808", highlightthickness=0, **kwargs)
        self._decoded = decoded
        self._value = 0
        self._blank = False
        self._draw()

    def set_value(self, val: int):
        val &= 0xFF
        if self._value != val or self._blank:
            self._value = val
            self._blank = False
            self._draw()

    def blank(self):
        if not self._blank:
            self._blank = True
            self._draw()

    def _bits(self) -> int:
        if self._blank:
            return 0
        return _DIGITS[self._value & 0x0F] if self._decoded else self._value & 0x7F

    def _draw(self):
        self.delete("all")
        T, G, mx, my = self._T, self._G, self._MX, self._MY
        W, H = self._W - 2 * mx, self._H - 2 * my
        H2 = H // 2
        bits = self._bits()

        def h_seg(x, y, w):
            return [x + G, y, x + w - G, y, x + w - G - T // 2, y + T, x + G + T // 2, y + T]

        def v_seg(x, y, hh):
            return [x, y + G, x + T, y + G + T // 2, x + T, y + hh - G - T // 2, x, y + hh - G]

        segs = [
            (0, h_seg(mx, my, W)),
            (1, v_seg(mx + W - T, my, H2)),
            (2, v_seg(mx + W - T, my + H2, H2)),
            (3, h_seg(mx, my + H, W)),
            (4, v_seg(mx, my + H2, H2)),
            (5, v_seg(mx, my, H2)),
            (6, h_seg(mx, my + H2, W)),
        ]
        for bit, pts in segs:
            color = self._ON if (bits >> bit) & 1 else self._OFF
            self.create_polygon(pts, fill=color, outline=color)


class DualSevenSeg(tk.Frame):
    """Two decoded 7-segment digits -- hi nibble=left, lo nibble=right."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#080808", **kwargs)
        self._value = None
        self._left = SevenSeg(self, decoded=True)
        self._right = SevenSeg(self, decoded=True)
        self._left.pack(side="left", padx=3, pady=6)
        self._right.pack(side="left", padx=3, pady=6)
        self.blank()

    def set_value(self, val: int):
        val &= 0xFF
        if self._value != val:
            self._value = val
            self._left.set_value((val >> 4) & 0x0F)
            self._right.set_value(val & 0x0F)

    def blank(self):
        self._value = -1
        self._left.blank()
        self._right.blank()


class WorkbenchPanel(tk.Frame):
    """Workbench 1 -- switch banks, LED bar, and three segment displays.

    Inert until the calculator is switched on -- call set_power(True/False)
    (wired to Calculator's power state via main_window.py) to enable or
    disable the whole board, same as Qt's setEnabled(on).
    """

    def __init__(self, parent, cpu, **kwargs):
        super().__init__(parent, bg="#c0c0c0", **kwargs)
        self.cpu = cpu
        self._powered = False
        self._build()
        self._install_hooks()
        self._set_enabled(False)

    # -- power control ------------------------------------------------------

    def set_power(self, on: bool):
        self._powered = on
        self._set_enabled(on)
        if not on:
            self._leds.set_value(0)
            self._seg1.set_value(0)
            self._seg2.blank()
            self._seg3.blank()

    def _set_enabled(self, on: bool):
        state = "normal" if on else "disabled"
        for sw in self._sw1._switches + self._sw2._switches:
            sw.configure(cursor="hand2" if on else "arrow")
        # Canvas-based switches have no native "disabled" state that blocks
        # clicks the way a real widget's state=disabled would -- gate the
        # actual write instead (see _sw1_write/_sw2_write below), which is
        # the behaviourally-important part (writes are ignored while off).

    # -- reset ----------------------------------------------------------------

    def reset(self):
        """Reset switches to OFF and blank outputs -- board stays powered,
        only state clears (unlike set_power(False))."""
        self._sw1.reset()
        self._sw2.reset()
        self._leds.set_value(0)
        self._seg1.set_value(0)
        self._seg2.blank()
        self._seg3.blank()

    def sync_from_ram(self):
        """Pull current port values from RAM -- call when the panel becomes
        visible, matching Qt's showEvent() sync. Only pulls a "touched"
        port's value; an untouched port stays blank/off, same reasoning
        as SevenSegDec.blank()'s docstring in the Qt source."""
        if not self._powered:
            return
        touched = self.cpu.ram_touched
        self._leds.set_value(self.cpu.ram[ADDR_LED] if touched[ADDR_LED] else 0)
        self._seg1.set_value(self.cpu.ram[ADDR_SEG1] if touched[ADDR_SEG1] else 0)
        if touched[ADDR_SEG2]:
            self._seg2.set_value(self.cpu.ram[ADDR_SEG2])
        else:
            self._seg2.blank()
        if touched[ADDR_SEG3]:
            self._seg3.set_value(self.cpu.ram[ADDR_SEG3])
        else:
            self._seg3.blank()

    # -- construction -----------------------------------------------------

    def _build(self):
        root = tk.Frame(self, bg="#c0c0c0")
        root.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(root, bg="#c0c0c0")
        left.pack(side="left", fill="y", padx=(0, 20))

        self._sw1 = SwitchBank(left, "8-Bit Switch Bank 1", on_value_changed=self._sw1_write)
        self._sw1.pack(pady=4)
        self._sw2 = SwitchBank(left, "8-Bit Switch Bank 2", on_value_changed=self._sw2_write)
        self._sw2.pack(pady=4)

        tk.Label(left, text="8-Bit LEDs", bg="#c0c0c0", font=("Arial", 12, "bold")).pack(anchor="w", pady=(8, 2))
        self._leds = LEDBar(left)
        self._leds.pack()

        right = tk.Frame(root, bg="#c0c0c0")
        right.pack(side="left", fill="y")

        cols = tk.Frame(right, bg="#c0c0c0")
        cols.pack()
        for i, title in enumerate(["7-Seg\nUn-Dec", "7-Seg\nDec", "Dual 7-Seg\nDecoded"]):
            tk.Label(cols, text=title, bg="#c0c0c0", font=("Arial", 12, "bold"),
                     justify="center").grid(row=0, column=i, padx=10)

        self._seg1 = SevenSeg(cols, decoded=False)
        self._seg2 = SevenSeg(cols, decoded=True)
        self._seg3 = DualSevenSeg(cols)
        self._seg1.grid(row=1, column=0, padx=10, pady=6)
        self._seg2.grid(row=1, column=1, padx=10, pady=6)
        self._seg3.grid(row=1, column=2, padx=10, pady=6)

    def _install_hooks(self):
        def _guard(fn):
            def _inner(val):
                if self._powered:
                    fn(val)
            return _inner

        self.cpu._write_hooks[ADDR_LED] = _guard(self._leds.set_value)
        self.cpu._write_hooks[ADDR_SEG1] = _guard(self._seg1.set_value)
        self.cpu._write_hooks[ADDR_SEG2] = _guard(self._seg2.set_value)
        self.cpu._write_hooks[ADDR_SEG3] = _guard(self._seg3.set_value)

    # -- switch write helpers -----------------------------------------------

    def _sw1_write(self, val: int):
        if self._powered:
            self.cpu.ram[ADDR_SW1] = val & 0xFF

    def _sw2_write(self, val: int):
        if self._powered:
            self.cpu.ram[ADDR_SW2] = val & 0xFF
