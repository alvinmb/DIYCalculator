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

"""Reusable LED-style readouts and status-flag indicators."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel

from ..styles import C


class LEDDisplay(QLabel):
    def __init__(self, width=3, box_width=None, parent=None):
        """LCD-style hex value display.

        ``width``     — number of hex digits in the formatted value
                        (e.g. ``2`` -> ``$XX``, ``4`` -> ``$XXXX``).
        ``box_width`` — optional override for sizing only.  Pass a
                        larger value than ``width`` to render a narrow
                        register inside a wider box so several
                        displays line up to the same physical size.
        """
        super().__init__(parent)
        self._width = width
        self._box_width = box_width if box_width is not None else width
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        font = QFont("Courier New", 14, QFont.Bold)
        self.setFont(font)
        self.setStyleSheet(f"""
            QLabel {{
                background: {C['lcd_bg']};
                color: #000;
                border: 2px inset {C['btn_bdr']};
                padding: 2px 7px;
                font-family: 'Courier New';
                font-size: 14pt;
                font-weight: bold;
            }}
        """)
        # Width scales with the requested *box* character count (so
        # several displays can share an identical pixel width even when
        # they hold values of different lengths).
        self.setFixedWidth(self._box_width * 14 + 24)
        self.setFixedHeight(30)
        self.setValue(0)  # moved after font/alignment so display renders correctly

    def setValue(self, val):
        self._val = val
        if self._width <= 4:
            self.setText(f"${val:0{self._width}X}")
        else:
            self.setText(f"{val:08b}")

    def setValueBin(self, val, bits=8):
        fmt = f"{{:0{bits}b}}"
        self.setText(fmt.format(val & ((1 << bits) - 1)))
        self._val = val


class FlagLight(QLabel):
    """LCD-style status-flag indicator with three visual states.

    The widget renders **just the value** inside a recessed LCD-style
    box; the flag's letter (C / Z / N / V / I / O) is expected to be
    shown by a separate header label placed above the widget by the
    parent layout.

    States:
      - ``unknown`` — never written by CPU; shows ``x`` in italic grey.
      - ``off``     — flag clear; shows ``0`` in black.
      - ``on``      — flag set;   shows ``1`` in bold red.
    """

    def __init__(self, name="", parent=None):
        super().__init__(parent)
        self._name = name           # kept for backwards compatibility
        self._on = False
        self._touched = False       # False -> render as "x" (unknown)
        self.setAlignment(Qt.AlignCenter)
        font = QFont("Courier New", 14, QFont.Bold)
        self.setFont(font)
        self.setFixedSize(36, 30)
        self._update()

    def setOn(self, on):
        """Mark this flag as having been written by the CPU, with the given value."""
        self._on = bool(on)
        self._touched = True
        self._update()

    def setUnknown(self):
        """Mark this flag as never-written; render as ``x``."""
        self._touched = False
        self._update()

    def _update(self):
        # Common LCD-style frame for all three states.
        base = (
            f"background:{C['lcd_bg']}; "
            f"border:2px inset {C['btn_bdr']}; "
            "font-family:'Courier New'; "
            "font-size:14pt; "
        )
        if not self._touched:
            self.setText("x")
            self.setStyleSheet(
                base + f"color:{C['grey']}; font-style:italic; font-weight:bold;"
            )
            return
        if self._on:
            self.setText("1")
            self.setStyleSheet(
                base + f"color:{C['red']}; font-weight:bold;"
            )
        else:
            self.setText("0")
            self.setStyleSheet(
                base + f"color:{C['lcd_fg']}; font-weight:bold;"
            )
