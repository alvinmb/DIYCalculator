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

"""Disassembler panel — shows decoded instructions starting at a chosen PC."""

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QPlainTextEdit,
    QVBoxLayout, QHBoxLayout,
)

from ..styles import C


class DisassemblerPanel(QWidget):
    def __init__(self, cpu, parent=None):
        super().__init__(parent)
        self.cpu = cpu
        self.setWindowTitle("Assembler / Disassembler")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        nav = QHBoxLayout()
        nav.addWidget(QLabel("From:"))
        self.addr_edit = QLineEdit("0000")
        self.addr_edit.setFixedWidth(55)
        self.dis_btn = QPushButton("Disassemble")
        self.dis_btn.setToolTip(
            "Disassemble 32 instructions starting at the address typed in the box."
        )
        self.dis_btn.clicked.connect(self._disassemble)
        nav.addWidget(self.addr_edit)
        nav.addWidget(self.dis_btn)
        nav.addStretch()
        layout.addLayout(nav)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Courier New", 11))
        layout.addWidget(self.output)

        self._disassemble()

    def _disassemble(self):
        try:
            addr = int(self.addr_edit.text(), 16)
        except ValueError:
            addr = 0
        lines = self.cpu.disassemble_at(addr, 32)
        text = ""
        for (pc, op, mnem, operand) in lines:
            text += f"  ${pc:04X}:  {op:02X}  {mnem:<6} {operand}\n"
        self.output.setPlainText(text)

    def refresh_at_pc(self, pc):
        self.addr_edit.setText(f"{pc:04X}")
        self._disassemble()
