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

The three 7-segment displays use the same photographic assets as the
Qt build (BITMAPS/USEGn.BMP for the un-decoded display, one file per
raw 7-bit value 0-127; BITMAPS/DSEGx.BMP for the decoded displays, one
file per hex digit 0-F plus DSEGG.BMP for the blank/off glyph -- real
segments render green-when-lit / dark-red-when-off, straight from the
photo). tkinter's PhotoImage has no built-in BMP decoder and no
built-in arbitrary-ratio resize (only GIF/PGM/PPM/PNG, and only
integer zoom/subsample scaling, without adding a Pillow runtime
dependency) -- so rather than either drawing vector approximations or
adding Pillow as a shipped dependency, all 145 BMPs were pre-converted
*once* (a dev-time-only step, using Pillow purely as a build tool, the
same way an image would be exported by hand in an image editor) to
PNGs already scaled to the display size (63x120, matching Qt's
SevenSegImage/SevenSegDec). Those PNGs live alongside their source
BMPs in BITMAPS/ and are loaded at runtime with plain
tk.PhotoImage(file=...), which decodes PNG natively -- no Pillow
import anywhere in this file or at app runtime.

Not ported: the switch-click .wav sound (QSound has no tkinter
equivalent -- same already-flagged Sound gap in TKINTER_MIGRATION.md).
"""

from __future__ import annotations

import tkinter as tk

try:
    from beboputer_v7.paths import resource_path
except ImportError:  # pragma: no cover
    import os

    def resource_path(*parts):
        return os.path.join(*parts)

ADDR_SW1 = 0xF000
ADDR_SW2 = 0xF001
ADDR_LED = 0xF022
ADDR_SEG1 = 0xF021
ADDR_SEG2 = 0xF023
ADDR_SEG3 = 0xF024

# Suffix for each nibble value 0-F in the DSEGx.png filenames; 'G' is
# the blank/off glyph (DSEGG.png), not a real digit.
_DSEG_SUFFIX = "0123456789ABCDEF"


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
    """Row of 8 green LEDs driven by a byte value.

    Geometry is matched to ToggleSwitch/SwitchBank so each LED sits
    directly below its corresponding switch, same intent as the Qt
    version's LEDBar (which spells out the matching pitch math in its
    own docstring):
      switch width = 30px, switch gap = 6px (3px pack padx each side)
        -> pitch = 36px, first switch center = 3 + 30/2 = 18px
      LED diameter = 24px, LED gap = 12px -> pitch = 36px (same as
        switches, so the per-LED offset from the switch above it stays
        constant across all 8, not just the first)
      X0 = 18 - 24/2 = 6px -- centers LED[0] under Switch[0]
    """

    _D, _SP, _X0 = 24, 12, 6

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


class SevenSeg(tk.Label):
    """Single 7-segment digit, rendered from the real BITMAPS/*.BMP
    photos (pre-scaled to PNG at 63x120 -- see module docstring), same
    as the Qt version's SevenSegImage/SevenSegDec.

    decoded=False -- raw 7-bit value (bits 0-6 = segments a-g) selects
                     BITMAPS/USEG{val}.png directly (one photo per
                     value, 0-127 -- no bit-to-segment math needed).
    decoded=True  -- low nibble of value selects BITMAPS/DSEG{hex}.png
                     (0-F); blank() shows BITMAPS/DSEGG.png, the true
                     off glyph.
    """

    _W, _H = 63, 120

    # One shared cache per class, keyed by "USEG3" / "DSEGA" / "DSEGG"
    # -- every digit position (seg1/seg2/seg3's four sub-digits) reuses
    # the same loaded tk.PhotoImage instead of re-decoding the PNG.
    _cache: dict[str, "tk.PhotoImage | None"] = {}

    def __init__(self, parent, decoded=True, **kwargs):
        super().__init__(parent, width=self._W, height=self._H,
                          bg="#080808", bd=0, highlightthickness=0, **kwargs)
        self._decoded = decoded
        self._value = -1  # force the first render to actually load an image
        self._blank = False
        if decoded:
            self.blank()
        else:
            self.set_value(0)

    def set_value(self, val: int):
        val &= 0x0F if self._decoded else 0x7F
        if self._value == val and not self._blank:
            return
        self._value = val
        self._blank = False
        self._render()

    def blank(self):
        """Show the true off/blank glyph -- only meaningful for decoded
        digits (DSEGG.png); set_value(0) would light up '0' instead."""
        if not self._decoded:
            self.set_value(0)
            return
        if self._blank:
            return
        self._blank = True
        self._render()

    def _asset_name(self) -> str:
        if self._decoded:
            suffix = "G" if self._blank else _DSEG_SUFFIX[self._value]
            return f"DSEG{suffix}"
        return f"USEG{self._value}"

    def _render(self):
        name = self._asset_name()
        img = self._cache.get(name)
        if img is not None:
            # _cache is a CLASS-level dict, shared by every SevenSeg
            # instance -- but a tk.PhotoImage belongs to whichever Tcl
            # interpreter (tk.Tk() root) was current when it was created.
            # A single real run of the app only ever has one root for its
            # whole lifetime, so this is normally a non-issue -- but
            # anything that creates more than one root in the same
            # process (e.g. a test suite building a fresh BebopMain per
            # test) can leave a stale PhotoImage in the cache pointing at
            # an interpreter that's since been destroyed; reusing it then
            # raises "image ... doesn't exist" instead of rendering.
            # Touching .width() is a cheap way to confirm the underlying
            # Tcl image is still alive before trusting the cache.
            try:
                img.width()
            except tk.TclError:
                img = None
                self._cache.pop(name, None)
        if name not in self._cache:
            try:
                img = tk.PhotoImage(file=resource_path("BITMAPS", f"{name}.png"))
            except tk.TclError:
                img = None  # missing/corrupt asset -- fall back to a blank square
            self._cache[name] = img
        if img is not None:
            self.configure(image=img)
            self.image = img  # keep a reference -- Tk drops PhotoImages with none
        else:
            self.configure(image="")
            self.image = None


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
        # LEDBar (228px) is narrower than the switch rows (288px), so
        # pack()'s default center anchor was shifting it ~30px right of
        # the switches above -- anchor="w" flushes its left edge to
        # match theirs instead.
        self._leds.pack(anchor="w")

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
