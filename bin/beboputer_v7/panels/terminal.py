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

"""Terminal — CRT-style output device driven by memory-mapped port $F028.

This is a Beboputer peripheral, not a diagnostic tool.
System / emulator messages go to the Message Display panel instead.

Screen state is controlled by the calculator's On/Off button:
  • Off  →  screen is black  (write_char calls are silently discarded)
  • On   →  screen is white  (characters from $F028 writes are rendered)

The CPU write-hook for address $F028 is registered in main_window.py so
that any  STORE ($F028), A  instruction routes ACC directly to write_char.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QTextEdit, QVBoxLayout, QFrame,
)

# ── screen stylesheets ────────────────────────────────────────────────────────

_CSS_OFF = """
    QTextEdit {
        background: #000000;
        color:       #000000;
        border:      none;
        font-family: 'Courier New';
        font-size:   22px;
    }
"""

_CSS_ON = """
    QTextEdit {
        background: #ffffff;
        color:       #000000;
        border:      none;
        font-family: 'Courier New';
        font-size:   22px;
    }
"""


class Terminal(QWidget):
    """CRT-style output device driven by port $F028."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._powered = False
        self._build()

    # ── construction ──────────────────────────────────────────────────────────

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(0)

        # outer raised bevel — mimics a monitor casing
        casing = QFrame()
        casing.setFrameShape(QFrame.Box)
        casing.setFrameShadow(QFrame.Raised)
        casing.setLineWidth(4)
        casing.setMidLineWidth(2)
        casing.setStyleSheet("background: #808080;")

        mid = QVBoxLayout(casing)
        mid.setContentsMargins(8, 8, 8, 8)
        mid.setSpacing(0)

        # inner sunken bezel — the screen surround
        bezel = QFrame()
        bezel.setFrameShape(QFrame.Box)
        bezel.setFrameShadow(QFrame.Sunken)
        bezel.setLineWidth(3)
        bezel.setMidLineWidth(1)
        bezel.setStyleSheet("background: #404040;")

        inner = QVBoxLayout(bezel)
        inner.setContentsMargins(4, 4, 4, 4)
        inner.setSpacing(0)

        # the screen itself
        self.screen = QTextEdit()
        self.screen.setReadOnly(True)
        self.screen.setFont(QFont("Courier New", 20))
        self.screen.setFrameShape(QFrame.NoFrame)
        self.screen.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.screen.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.screen.setWordWrapMode(1)
        inner.addWidget(self.screen)

        mid.addWidget(bezel)
        outer.addWidget(casing)

        # start in the powered-off state
        self._apply_power(False)

    # ── power control ─────────────────────────────────────────────────────────

    def _apply_power(self, on: bool):
        self._powered = on
        if on:
            self.screen.setStyleSheet(_CSS_ON)
        else:
            self.screen.setStyleSheet(_CSS_OFF)
            self.screen.clear()

    def set_power(self, on: bool):
        """Slot — connected to Calculator.power_changed signal."""
        self._apply_power(on)

    # ── device output ─────────────────────────────────────────────────────────

    def write_char(self, ch: int):
        """Receive one byte from port $F028 and paint it on the screen.

        Printable ASCII (32–126) is rendered as the corresponding character;
        0x0A (\\n) moves to the next line.  All other values are ignored.
        Silently discarded when the terminal is powered off.
        """
        if not self._powered:
            return
        if 32 <= ch <= 126:
            self.screen.insertPlainText(chr(ch))
        elif ch == 0x0A:
            self.screen.insertPlainText("\n")
