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

"""System Clock dialog — set the simulated CPU clock speed."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QFormLayout, QVBoxLayout, QHBoxLayout, QMessageBox,
)

from ..styles import C


_LBL_STYLE = (
    "color: #000; font-weight: bold; font-size: 10px;"
)

_FIELD_STYLE = (
    f"background: {C['lcd_bg']}; color: #000; "
    f"border: 2px inset {C['btn_bdr']}; "
    "font-family: 'Courier New'; font-weight: bold; font-size: 11pt; "
    "padding: 1px 5px; min-height: 22px;"
)

_STATUS_STYLE = (
    f"color: {C['green_mid']}; font-size: 10px;"
)


class SystemClockDialog(QDialog):
    """Styled System Clock speed dialog, matching I/O map font conventions."""

    def __init__(self, current_hz, parent=None):
        super().__init__(parent)
        self.setWindowTitle("System Clock")
        self.setFixedSize(320, 160)
        self._hz = current_hz
        self._build()

    # ── Build ──────────────────────────────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 16)

        # Form row
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(8)

        self._hz_edit = QLineEdit(str(self._hz))
        self._hz_edit.setStyleSheet(_FIELD_STYLE)
        self._hz_edit.setAlignment(Qt.AlignRight)
        self._hz_edit.returnPressed.connect(self._apply)

        lbl = QLabel("Clock Speed (Hz):")
        lbl.setStyleSheet(_LBL_STYLE)
        form.addRow(lbl, self._hz_edit)

        root.addLayout(form)

        # Hint label
        hint = QLabel("Range: 1 – 10 000 Hz")
        hint.setStyleSheet(_LBL_STYLE)
        hint.setAlignment(Qt.AlignRight)
        root.addWidget(hint)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("&OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._apply)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        root.addLayout(btn_row)

    # ── Slots ──────────────────────────────────────────────────────────────

    def _apply(self):
        try:
            val = int(self._hz_edit.text().strip())
            if not (1 <= val <= 10000):
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Invalid Value",
                                "Please enter a whole number between 1 and 10 000.")
            self._hz_edit.setFocus()
            self._hz_edit.selectAll()
            return
        self._hz = val
        self.accept()

    # ── Result ─────────────────────────────────────────────────────────────

    def value(self):
        """Return the validated Hz value after accept()."""
        return self._hz
