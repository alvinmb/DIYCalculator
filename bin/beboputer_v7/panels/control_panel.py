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

"""RUN / STEP / HALT / RESET buttons, address/data bus readout, switches."""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QCheckBox, QLineEdit, QGroupBox,
    QVBoxLayout, QHBoxLayout, QFormLayout,
)

from ..styles import C


class ControlPanel(QWidget):
    sig_run   = pyqtSignal()
    sig_step  = pyqtSignal()
    sig_reset = pyqtSignal()
    sig_halt  = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Switch Panel")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("◈ CONTROL PANEL")
        title.setStyleSheet(f"color:{C['blue']}; font-weight:bold; font-size:13px; letter-spacing:2px;")
        layout.addWidget(title)

        btn_row = QHBoxLayout()
        self.run_btn   = self._btn("▶  RUN",   self.C_green,  self.sig_run)
        self.step_btn  = self._btn("⏭  STEP",  self.C_amber,  self.sig_step)
        self.halt_btn  = self._btn("⏸  HALT",  self.C_red,    self.sig_halt)
        self.reset_btn = self._btn("↺  RESET", self.C_blue,   self.sig_reset)
        for b in [self.run_btn, self.step_btn, self.halt_btn, self.reset_btn]:
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        # Address & Data bus display
        bus_box = QGroupBox("Address / Data Bus")
        bus_layout = QFormLayout(bus_box)
        self.addr_disp = QLineEdit("$0000")
        self.addr_disp.setReadOnly(True)
        self.data_disp = QLineEdit("$00")
        self.data_disp.setReadOnly(True)
        # Halve the width and bump the font 2pt larger than the default (~11px → 14px)
        self.data_disp.setMaximumWidth(60)
        _f = self.data_disp.font()
        _pt = _f.pointSize() if _f.pointSize() > 0 else 8
        _f.setPointSize(_pt + 2)
        self.data_disp.setFont(_f)
        bus_layout.addRow("Address Bus:", self.addr_disp)
        bus_layout.addRow("Data Bus:",    self.data_disp)
        layout.addWidget(bus_box)

        # Data switches (8 toggle checkboxes)
        sw_box = QGroupBox("Data Switches  (manual input)")
        sw_layout = QHBoxLayout(sw_box)
        self.switches = []
        for i in range(7, -1, -1):
            cb = QCheckBox(str(i))
            cb.setFixedWidth(38)
            sw_layout.addWidget(cb)
            self.switches.insert(0, cb)
        layout.addWidget(sw_box)

        # Enter button
        enter_row = QHBoxLayout()
        self.enter_btn = QPushButton("ENTER  ↵")
        self.enter_btn.setStyleSheet(
            f"background-color:{C['btn_bg']}; color:{C['green']}; "
            f"border:1px solid {C['btn_bdr']}; "
            f"border-top-color:{C['border_lt']}; border-left-color:{C['border_lt']}; "
            "border-radius:2px; padding:3px 10px; font-weight:bold;"
        )
        enter_row.addStretch()
        enter_row.addWidget(self.enter_btn)
        layout.addLayout(enter_row)

        layout.addStretch()

    _BTN_BASE = (
        f"background-color:{C['btn_bg']};"
        f"border:1px solid {C['btn_bdr']};"
        f"border-top-color:{C['border_lt']};"
        f"border-left-color:{C['border_lt']};"
        "border-radius:2px;"
        "padding:3px 8px;"
        "font-weight:bold;"
    )
    C_green = _BTN_BASE + f"color:{C['green']};"
    C_amber = _BTN_BASE + f"color:{C['amber']};"
    C_red   = _BTN_BASE + f"color:{C['red']};"
    C_blue  = _BTN_BASE + f"color:{C['blue']};"

    def _btn(self, text, style, signal):
        b = QPushButton(text)
        b.setStyleSheet(style)
        b.setMinimumHeight(30)
        b.clicked.connect(signal.emit)
        return b

    def get_switch_value(self):
        val = 0
        for i, cb in enumerate(self.switches):
            if cb.isChecked():
                val |= (1 << i)
        return val

    def set_bus(self, addr, data):
        self.addr_disp.setText(f"${addr:04X}")
        self.data_disp.setText(f"${data:02X}")
