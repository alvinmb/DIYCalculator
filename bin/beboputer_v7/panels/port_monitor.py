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

"""I/O Ports Display - memory-mapped I/O monitor.

Shows the three memory-mapped I/O locations used by the Beboputer:

    $F031   Output to Main Display      (character to print)
    $F032   Output to LED row           (binary bit pattern)
    $F011   Input from Buttons          (current + previous value)
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QGroupBox,
    QVBoxLayout, QGridLayout,
)

from ..styles import C


# Memory-mapped I/O addresses
ADDR_DISPLAY = 0xF031
ADDR_LEDS    = 0xF032
ADDR_BUTTONS = 0xF011


_GROUP_STYLE = (
    "QGroupBox { color: " + C["red"] + "; font-weight: bold; font-size: 10px; "
    "border: 2px groove " + C["btn_bdr"] + "; margin-top: 8px; padding-top: 5px; }"
    "QGroupBox::title { subcontrol-origin: margin; left: 10px; "
    "color: " + C["blue"] + "; background: " + C["panel"] + "; padding: 0 3px; }"
)

_VALUE_STYLE = (
    "background: " + C["lcd_bg"] + "; color: #000; "
    "border: 2px inset " + C["btn_bdr"] + "; "
    "font-family: 'Courier New'; font-weight: bold; font-size: 11pt; "
    "padding: 1px 5px; min-height: 22px;"
)

# Maximum width for the value display fields.
_FIELD_MAX_WIDTH = 150


def _value_box(title):
    box = QGroupBox(title)
    box.setStyleSheet(_GROUP_STYLE)
    box.setMaximumWidth(_FIELD_MAX_WIDTH)
    v = QVBoxLayout(box)
    v.setContentsMargins(6, 5, 6, 5)
    lbl = QLabel("---")
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(_VALUE_STYLE)
    v.addWidget(lbl)
    return box, lbl


def _addr_label(text):
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet("color: " + C["blue"] + "; font-weight: bold; font-size: 10px;")
    return lbl


class PortMonitor(QWidget):
    def __init__(self, cpu, parent=None):
        super().__init__(parent)
        self.cpu = cpu
        self.setWindowTitle("I/O Ports Display")
        self._prev_button_val = None
        self._last_button_val = 0   # tracks previous port value across refresh() calls
        self._build()

    def _build(self):
        outer = QGridLayout(self)
        outer.setHorizontalSpacing(6)
        outer.setVerticalSpacing(5)
        outer.setContentsMargins(8, 6, 8, 6)
        outer.setColumnStretch(0, 0)
        outer.setColumnStretch(1, 1)
        outer.setColumnStretch(2, 1)

        outer.addWidget(_addr_label("$F031"), 0, 0)
        disp_box, self.lbl_display_hex = _value_box("O/P to Main Display")
        char_box, self.lbl_display_char = _value_box("Character etc")
        outer.addWidget(disp_box, 0, 1, Qt.AlignHCenter)
        outer.addWidget(char_box, 0, 2, Qt.AlignHCenter)

        outer.addWidget(_addr_label("$F032"), 1, 0)
        led_box, self.lbl_led_hex = _value_box("O/P to LED's")
        bin_box, self.lbl_led_bin = _value_box("Binary")
        outer.addWidget(led_box, 1, 1, Qt.AlignHCenter)
        outer.addWidget(bin_box, 1, 2, Qt.AlignHCenter)

        bracket = QLabel("$F011")
        bracket.setAlignment(Qt.AlignCenter)
        blue = C["blue"]
        bracket.setStyleSheet(
            "color: " + blue + "; font-weight: bold; font-size: 10px; "
            "border-left: 2px solid " + blue + "; "
            "border-top: 2px solid " + blue + "; "
            "border-bottom: 2px solid " + blue + "; "
            "padding: 3px 5px;"
        )
        outer.addWidget(bracket, 2, 0, 2, 1)

        cur_box = QGroupBox("I/P from Buttons")
        cur_box.setStyleSheet(_GROUP_STYLE)
        cur_box.setMaximumWidth(_FIELD_MAX_WIDTH)
        v = QVBoxLayout(cur_box)
        v.setContentsMargins(6, 5, 6, 5)
        self.btn_edit = QLineEdit("$00")
        self.btn_edit.setMaxLength(3)
        self.btn_edit.setAlignment(Qt.AlignCenter)
        self.btn_edit.setStyleSheet(_VALUE_STYLE)
        self.btn_edit.editingFinished.connect(self._on_button_changed)
        v.addWidget(self.btn_edit)
        outer.addWidget(cur_box, 2, 1, Qt.AlignHCenter)

        ann_box, self.lbl_btn_ann = _value_box("Annotation")
        outer.addWidget(ann_box, 2, 2, Qt.AlignHCenter)

        old_box, self.lbl_old_btn = _value_box("Old I/P from Button")
        outer.addWidget(old_box, 3, 1, Qt.AlignHCenter)

        old_ann_box, self.lbl_old_btn_ann = _value_box("Annotation")
        outer.addWidget(old_ann_box, 3, 2, Qt.AlignHCenter)

        self.lbl_display_hex.setText("$XX")
        self.lbl_display_char.setText("---")
        self.lbl_led_hex.setText("---")
        self.lbl_led_bin.setText("XXXXXXXX")
        self.lbl_btn_ann.setText("---")
        self.lbl_old_btn.setText("---")
        self.lbl_old_btn_ann.setText("---")

    def _on_button_changed(self):
        txt = self.btn_edit.text().strip().lstrip("$")
        if txt.lower().startswith("0x"):
            txt = txt[2:]
        try:
            val = int(txt, 16) & 0xFF
        except ValueError:
            return
        prev = self.cpu.ram[ADDR_BUTTONS]
        if prev != val:
            self._prev_button_val = prev
        self.cpu.ram[ADDR_BUTTONS] = val
        self.btn_edit.setText("$%02X" % val)
        self.refresh()

    @staticmethod
    def _char_annot(b):
        if 32 <= b < 127:
            return "'" + chr(b) + "'"
        if 0x00 <= b <= 0x09:
            return "'" + str(b) + "'"          # raw digit
        if 0x0A <= b <= 0x0F:
            return "'" + chr(b - 0x0A + ord('A')) + "'"  # raw hex letter
        named = {0x07:"BEL",0x08:"BS",0x09:"TAB",0x0D:"CR",0x1B:"ESC"}
        return named.get(b, "---")

    def reset(self):
        """Clear all displayed values back to initial state (called on CPU reset)."""
        self._prev_button_val = None
        self._last_button_val = 0xFF  # idle sentinel
        self.lbl_display_hex.setText("$00")
        self.lbl_display_char.setText("---")
        self.lbl_led_hex.setText("$00")
        self.lbl_led_bin.setText("00000000")
        self.btn_edit.setText("$FF")
        self.lbl_btn_ann.setText("---")
        self.lbl_old_btn.setText("---")
        self.lbl_old_btn_ann.setText("---")

    def on_key_press(self, val):
        """Called by the $F011 write hook the moment a button is written.
        Captures the value before the read-clear strobe wipes ram[$F011]."""
        if val != self._last_button_val:
            self._prev_button_val = self._last_button_val
            self._last_button_val = val
        if not self.btn_edit.hasFocus():
            self.btn_edit.setText("$%02X" % val)
        self.lbl_btn_ann.setText(self._char_annot(val))
        if self._prev_button_val is not None:
            self.lbl_old_btn.setText("$%02X" % self._prev_button_val)
            self.lbl_old_btn_ann.setText(self._char_annot(self._prev_button_val))

    def refresh(self):
        ram = self.cpu.ram
        d = ram[ADDR_DISPLAY]
        self.lbl_display_hex.setText("$%02X" % d)
        self.lbl_display_char.setText(self._char_annot(d))
        led = ram[ADDR_LEDS]
        self.lbl_led_hex.setText("$%02X" % led)
        self.lbl_led_bin.setText(format(led, "08b"))
        # Button section: use _last_button_val set by on_key_press() — do NOT
        # read ram[ADDR_BUTTONS] directly because the read-clear strobe in
        # main_window resets it to $FF the instant the CPU reads it.
        cur = self._last_button_val
        if not self.btn_edit.hasFocus():
            self.btn_edit.setText("$%02X" % cur)
        self.lbl_btn_ann.setText(self._char_annot(cur))
        if self._prev_button_val is None:
            self.lbl_old_btn.setText("---")
            self.lbl_old_btn_ann.setText("---")
        else:
            self.lbl_old_btn.setText("$%02X" % self._prev_button_val)
            self.lbl_old_btn_ann.setText(self._char_annot(self._prev_button_val))
