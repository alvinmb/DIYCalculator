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

"""Workbench 1 — dual 8-bit switch input banks + LED / 7-segment outputs.

Port map
────────
Input   $F000   8-Bit Switch Bank 1  (bit 7 = left / MSB)
Input   $F001   8-Bit Switch Bank 2  (bit 7 = left / MSB)
Output  $F020   8-Bit LED Display
Output  $F021   7-Segment un-decoded  (bits 0-6 → segments a-g directly)
Output  $F022   7-Segment decoded     (low nibble → hex digit 0-F)
Output  $F023   Dual 7-Segment decoded (hi nibble = left digit, lo = right)
"""

import os

from PyQt5.QtCore  import Qt, QPoint, pyqtSignal
from PyQt5.QtGui   import QPainter, QColor, QPen, QBrush, QPolygon, QFont, QPixmap
from PyQt5.QtWidgets import (
    QDialog, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout, QGridLayout,
)

from ..paths import resource_path

# ── BITMAPS folder — resolved via resource_path for both source and bundle ──────
_BITMAPS_DIR = resource_path('BITMAPS')

# ── Switch click sound ────────────────────────────────────────────────────────
try:
    from PyQt5.QtMultimedia import QSound as _QSound
    _SWITCH_WAV = os.path.join(_BITMAPS_DIR, 'SWITCH.WAV')
    def _play_switch_sound():
        _QSound.play(_SWITCH_WAV)
except ImportError:
    def _play_switch_sound():
        pass

# ── port addresses ─────────────────────────────────────────────────────────────
ADDR_SW1  = 0xF000
ADDR_SW2  = 0xF001
ADDR_LED  = 0xF022
ADDR_SEG1 = 0xF021
ADDR_SEG2 = 0xF023
ADDR_SEG3 = 0xF024

# ── 7-segment encoding for hex digits 0-F ─────────────────────────────────────
# bit 0=a(top) 1=b(upper-right) 2=c(lower-right) 3=d(bottom)
# bit 4=e(lower-left) 5=f(upper-left) 6=g(middle)
_DIGITS = [
    0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07,
    0x7F, 0x6F, 0x77, 0x7C, 0x39, 0x5E, 0x79, 0x71,
]


# ══════════════════════════════════════════════════════════════════════════════
# Toggle Switch
# ══════════════════════════════════════════════════════════════════════════════

class ToggleSwitch(QWidget):
    """Single toggle switch.  Click to flip.
    Lever UP = OFF (red).  Lever DOWN = ON (green)."""

    changed = pyqtSignal(bool)

    _W, _H = 38, 58   # 30×46 scaled ×1.25

    def __init__(self, parent=None):
        super().__init__(parent)
        self._on = False
        self.setFixedSize(self._W, self._H)
        self.setCursor(Qt.PointingHandCursor)

    @property
    def is_on(self) -> bool:
        return self._on

    def set_on(self, on: bool):
        if self._on != on:
            self._on = on
            self.update()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._on = not self._on
            _play_switch_sound()
            self.changed.emit(self._on)
            self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self._W, self._H
        cx = W // 2

        # Housing base (bottom half)
        p.setPen(QPen(QColor("#2a1508"), 1))
        p.setBrush(QBrush(QColor("#5a3418")))
        p.drawRoundedRect(4, H // 2 + 4, W - 8, H // 2 - 8, 5, 5)

        # Lever: UP = OFF (red), DOWN = ON (green)
        lw, lh = 15, H // 2 + 5
        lx = cx - lw // 2
        ly = H // 2 - 5 if self._on else 3   # down when ON, up when OFF
        col = QColor("#00aa00") if self._on else QColor("#cc0000")

        p.setPen(QPen(QColor("#1a1a1a"), 1))
        p.setBrush(QBrush(col))
        p.drawRoundedRect(lx, ly, lw, lh, 3, 3)

        # Highlight strip on lever
        p.setPen(Qt.NoPen)
        hi = QColor("#55ee55") if self._on else QColor("#ff6666")
        p.setBrush(QBrush(hi))
        p.drawRoundedRect(lx + 2, ly + 2, lw - 4, 6, 2, 2)

        p.end()


# ══════════════════════════════════════════════════════════════════════════════
# 8-Bit Switch Bank
# ══════════════════════════════════════════════════════════════════════════════

class SwitchBank(QWidget):
    """Labelled row of 8 toggle switches representing one input byte."""

    value_changed = pyqtSignal(int)

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self._switches: list = []
        self._build(label)

    def _build(self, label: str):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(5, 3, 5, 3)
        vbox.setSpacing(4)

        lbl = QLabel(label)
        lbl.setStyleSheet("font-weight:bold; font-size:12px;")
        vbox.addWidget(lbl)

        row = QHBoxLayout()
        row.setSpacing(6)
        for _ in range(8):
            sw = ToggleSwitch()
            sw.changed.connect(lambda _on: self.value_changed.emit(self.value()))
            self._switches.append(sw)
            row.addWidget(sw)
        row.addStretch()
        vbox.addLayout(row)

    def value(self) -> int:
        v = 0
        for i, sw in enumerate(self._switches):
            if sw.is_on:
                v |= 1 << (7 - i)
        return v

    def reset(self):
        """Flip every switch back to OFF (no click sound) and push the
        resulting all-zero value out to whatever is listening."""
        for sw in self._switches:
            sw.set_on(False)
        self.value_changed.emit(self.value())


# ══════════════════════════════════════════════════════════════════════════════
# 8-Bit LED Bar  (output)
# ══════════════════════════════════════════════════════════════════════════════

class LEDBar(QWidget):
    """Row of 8 green LEDs driven by a byte value.

    Geometry is matched to ToggleSwitch so each LED sits directly
    below its corresponding switch:
      switch width = 38 px,  switch gap = 6 px  → pitch = 44 px
      LED diameter  = 30 px, LED gap    = 14 px → pitch = 44 px  ✓
      x0 = switch_bank_left_margin(5) + switch_half(19) - LED_half(15) = 9 px
    """

    _D  = 30   # LED diameter
    _SP = 14   # gap between LEDs  (D + SP = 44 = switch pitch)
    _X0 =  9   # left offset — centres LED[0] under Switch[0]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        D, SP, X0 = self._D, self._SP, self._X0
        self.setFixedSize(X0 + 8 * D + 7 * SP + X0, D + 18)

    def set_value(self, val: int):
        val &= 0xFF
        if self._value != val:
            self._value = val
            self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        D, SP, X0 = self._D, self._SP, self._X0
        y0 = 8

        for i in range(8):
            bit = (self._value >> (7 - i)) & 1
            x = X0 + i * (D + SP)

            p.setPen(QPen(QColor("#004400"), 1))
            p.setBrush(QBrush(QColor("#00cc00") if bit else QColor("#1a3a1a")))
            p.drawEllipse(x, y0, D, D)

            if bit:                                  # glint
                p.setPen(Qt.NoPen)
                p.setBrush(QBrush(QColor("#99ff99")))
                p.drawEllipse(x + 5, y0 + 4, D // 3, D // 3)

        p.end()


# ══════════════════════════════════════════════════════════════════════════════
# Un-decoded 7-Segment display — image-based  (output $F021)
# ══════════════════════════════════════════════════════════════════════════════

class SevenSegImage(QWidget):
    """Un-decoded 7-segment display using USEG0..USEG127 BMP images.

    Bits 0-6 of the value map directly to segments a-g.
    The BMP for value n is BITMAPS/USEGn.BMP (native 48×91 px).
    Displayed scaled to _W × _H keeping aspect ratio, centred on black.
    """

    # Scale to the same height as the painted SevenSeg widget.
    _W = 63    # 48 * (120/91) ≈ 63  (aspect-correct width at _H=120)
    _H = 120

    # Cache pixmaps so each file is only loaded once.
    _cache: dict = {}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = -1          # force first load
        self.setFixedSize(self._W, self._H)
        self.setStyleSheet("background: #080808;")

        self._lbl = QLabel(self)
        self._lbl.setAlignment(Qt.AlignCenter)
        self._lbl.setFixedSize(self._W, self._H)
        self._lbl.setStyleSheet("background: #080808;")

        self.set_value(0)

    def set_value(self, val: int):
        val &= 0x7F               # 7-bit un-decoded value
        if val == self._value:
            return
        self._value = val
        px = self._get_pixmap(val)
        if px:
            self._lbl.setPixmap(
                px.scaled(self._W, self._H,
                          Qt.KeepAspectRatio,
                          Qt.SmoothTransformation)
            )
        else:
            self._lbl.clear()

    @classmethod
    def _get_pixmap(cls, val: int):
        if val not in cls._cache:
            path = os.path.join(_BITMAPS_DIR, f'USEG{val}.BMP')
            px = QPixmap(path)
            cls._cache[val] = px if not px.isNull() else None
        return cls._cache[val]


# ══════════════════════════════════════════════════════════════════════════════
# Decoded 7-Segment display — image-based  (output $F022 / $F023)
# ══════════════════════════════════════════════════════════════════════════════

# Filename suffix for each nibble value 0-F; DSEGG is the blank/off image.
_DSEG_SUFFIX = ['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']


class SevenSegDec(QWidget):
    """Decoded 7-segment display using DSEG0..DSEGF BMP images.

    The low nibble of the value selects the digit image (0-F).
    DSEGG.BMP is shown when the display is blank (initial state).
    Same 48×91 native size as the undecoded images, displayed at 63×120.
    """

    _W = 63
    _H = 120

    _cache: dict = {}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = -1
        self.setFixedSize(self._W, self._H)
        self.setStyleSheet("background: #080808;")

        self._lbl = QLabel(self)
        self._lbl.setAlignment(Qt.AlignCenter)
        self._lbl.setFixedSize(self._W, self._H)
        self._lbl.setStyleSheet("background: #080808;")

        self.set_value(0)

    def set_value(self, val: int):
        val &= 0x0F
        if val == self._value:
            return
        self._value = val
        px = self._get_pixmap(val)
        if px:
            self._lbl.setPixmap(
                px.scaled(self._W, self._H,
                          Qt.KeepAspectRatio,
                          Qt.SmoothTransformation)
            )
        else:
            self._lbl.clear()

    @classmethod
    def _get_pixmap(cls, val: int):
        if val not in cls._cache:
            suffix = _DSEG_SUFFIX[val]
            path = os.path.join(_BITMAPS_DIR, f'DSEG{suffix}.BMP')
            px = QPixmap(path)
            cls._cache[val] = px if not px.isNull() else None
        return cls._cache[val]


# ══════════════════════════════════════════════════════════════════════════════
# 7-Segment Digit  (output)
# ══════════════════════════════════════════════════════════════════════════════

class SevenSeg(QWidget):
    """Single 7-segment digit on a black background.

    decoded=False  raw bits 0-6 map directly to segments a-g
    decoded=True   low nibble of value → 0-F digit shape
    """

    _W  = 80    # widget width  (64 × 1.25)
    _H  = 120   # widget height (96 × 1.25)
    _T  = 10    # segment thickness (8 × 1.25)
    _G  =  4    # gap at segment ends (3 × 1.25)
    _MX = 10    # left/right margin (8 × 1.25)
    _MY =  8    # top/bottom margin (6 × 1.25)

    _ON  = QColor("#dd2200")
    _OFF = QColor("#2a0600")

    def __init__(self, decoded: bool = True, parent=None):
        super().__init__(parent)
        self._decoded = decoded
        self._value   = 0
        self.setFixedSize(self._W, self._H)

    def set_value(self, val: int):
        val &= 0xFF
        if self._value != val:
            self._value = val
            self.update()

    def _bits(self) -> int:
        return _DIGITS[self._value & 0x0F] if self._decoded else self._value & 0x7F

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#080808"))

        T, G   = self._T, self._G
        mx, my = self._MX, self._MY
        W  = self._W - 2 * mx
        H  = self._H - 2 * my
        H2 = H // 2
        bits = self._bits()

        def ph(x, y, w):   # horizontal segment polygon
            return QPolygon([QPoint(x+G,       y),
                             QPoint(x+w-G,     y),
                             QPoint(x+w-G-T//2, y+T),
                             QPoint(x+G+T//2,  y+T)])

        def pv(x, y, h):   # vertical segment polygon
            return QPolygon([QPoint(x,   y+G),
                             QPoint(x+T, y+G+T//2),
                             QPoint(x+T, y+h-G-T//2),
                             QPoint(x,   y+h-G)])

        segs = [
            (0, ph(mx,         my,          W )),   # a – top
            (1, pv(mx+W-T,     my,          H2)),   # b – upper-right
            (2, pv(mx+W-T,     my+H2,       H2)),   # c – lower-right
            (3, ph(mx,         my+H,        W )),   # d – bottom
            (4, pv(mx,         my+H2,       H2)),   # e – lower-left
            (5, pv(mx,         my,          H2)),   # f – upper-left
            (6, ph(mx,         my+H2,       W )),   # g – middle
        ]

        p.setPen(Qt.NoPen)
        for bit, poly in segs:
            p.setBrush(QBrush(self._ON if (bits >> bit) & 1 else self._OFF))
            p.drawPolygon(poly)

        p.end()


class DualSevenSeg(QWidget):
    """Two decoded 7-segment digits — hi nibble = left, lo nibble = right."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        self._left  = SevenSegDec()
        self._right = SevenSegDec()
        layout.addWidget(self._left)
        layout.addWidget(self._right)
        self.setStyleSheet("background:#080808;")

    def set_value(self, val: int):
        val &= 0xFF
        if self._value != val:
            self._value = val
            self._left.set_value((val >> 4) & 0x0F)
            self._right.set_value(val & 0x0F)


# ══════════════════════════════════════════════════════════════════════════════
# Workbench Panel
# ══════════════════════════════════════════════════════════════════════════════

class WorkbenchPanel(QDialog):
    """Workbench 1 — switch banks, LED bar, and three segment displays.

    The panel is inert until the calculator is switched on.  Call
    set_power(True/False) — normally wired to Calculator.power_changed —
    to enable or disable the whole board.
    """

    def __init__(self, cpu, parent=None):
        super().__init__(parent)
        self.cpu      = cpu
        self._powered = False
        self.setWindowTitle("Workbench 1")
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )
        self._build()
        self._install_hooks()
        # Start disabled — mirrors calculator power-off state.
        self.setEnabled(False)

    # ── power control ─────────────────────────────────────────────────────────

    def set_power(self, on: bool):
        """Slot — wired to Calculator.power_changed in main_window.py."""
        self._powered = on
        self.setEnabled(on)
        if not on:
            # Blank all outputs so they don't show stale values.
            self._leds.set_value(0)
            self._seg1.set_value(0)
            self._seg2.set_value(0)
            self._seg3.set_value(0)

    # ── reset ──────────────────────────────────────────────────────────────────

    def reset(self):
        """Reset switches to OFF and blank all outputs. Called on the
        calculator's RESET button — unlike set_power(False), the board
        stays enabled/powered; only its state is cleared."""
        self._sw1.reset()
        self._sw2.reset()
        self._leds.set_value(0)
        self._seg1.set_value(0)
        self._seg2.set_value(0)
        self._seg3.set_value(0)

    # ── lifecycle ──────────────────────────────────────────────────────────────

    def closeEvent(self, ev):
        if getattr(self, '_app_closing', False):
            ev.accept()
        else:
            ev.ignore()
            self.hide()

    def showEvent(self, ev):
        """Sync displays with RAM when window becomes visible."""
        super().showEvent(ev)
        if self._powered:
            self._leds.set_value(self.cpu.ram[ADDR_LED])
            self._seg1.set_value(self.cpu.ram[ADDR_SEG1])
            self._seg2.set_value(self.cpu.ram[ADDR_SEG2])
            self._seg3.set_value(self.cpu.ram[ADDR_SEG3])

    # ── construction ───────────────────────────────────────────────────────────

    def _build(self):
        root = QHBoxLayout(self)
        root.setSpacing(25)
        root.setContentsMargins(15, 15, 15, 15)

        # ── left: switches + LED bar ──────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(8)

        self._sw1 = SwitchBank("8-Bit Switch Bank 1")
        self._sw2 = SwitchBank("8-Bit Switch Bank 2")
        self._sw1.value_changed.connect(self._sw1_write)
        self._sw2.value_changed.connect(self._sw2_write)

        left.addWidget(self._sw1)
        left.addWidget(self._sw2)

        led_lbl = QLabel("8-Bit LEDs")
        led_lbl.setStyleSheet("font-weight:bold; font-size:12px;")
        left.addWidget(led_lbl)

        self._leds = LEDBar()
        left.addWidget(self._leds)
        left.addStretch()
        root.addLayout(left)

        # ── right: 7-segment displays ─────────────────────────────────────
        right = QGridLayout()
        right.setHorizontalSpacing(20)
        right.setVerticalSpacing(8)

        for col, title in enumerate(
            ["7-Seg\nUn-Dec", "7-Seg\nDec", "Dual 7-Seg\nDecoded"]
        ):
            lbl = QLabel(title)
            lbl.setAlignment(Qt.AlignHCenter)
            lbl.setStyleSheet("font-weight:bold; font-size:12px;")
            right.addWidget(lbl, 0, col)

        self._seg1 = SevenSegImage()
        self._seg2 = SevenSegDec()
        self._seg3 = DualSevenSeg()

        right.addWidget(self._seg1, 1, 0, Qt.AlignHCenter)
        right.addWidget(self._seg2, 1, 1, Qt.AlignHCenter)
        right.addWidget(self._seg3, 1, 2, Qt.AlignHCenter)

        root.addLayout(right)

    def _install_hooks(self):
        # Wrap each display setter so it silently ignores writes when off.
        def _guard(fn):
            def _inner(val):
                if self._powered:
                    fn(val)
            return _inner

        self.cpu._write_hooks[ADDR_LED]  = _guard(self._leds.set_value)
        self.cpu._write_hooks[ADDR_SEG1] = _guard(self._seg1.set_value)
        self.cpu._write_hooks[ADDR_SEG2] = _guard(self._seg2.set_value)
        self.cpu._write_hooks[ADDR_SEG3] = _guard(self._seg3.set_value)

    # ── switch write helpers ───────────────────────────────────────────────────

    def _sw1_write(self, val: int):
        if self._powered:
            self.cpu.ram[ADDR_SW1] = val & 0xFF

    def _sw2_write(self, val: int):
        if self._powered:
            self.cpu.ram[ADDR_SW2] = val & 0xFF
