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

"""CPU register display panel.

Layout (matches the original DIY Calculator screenshot):

    +------------------+  +------------------+
    | Accumulator      |  | Program Counter  |
    +------------------+  +------------------+
    | Instruction Reg  |  | Index Reg        |
    +------------------+  +------------------+
    | Interrupt Vector |  | Stack Pointer    |
    +------------------+  +------------------+

    Status Reg:  I   O   N   Z   C

The "O" flag is the CPU's overflow flag (FLAG_V).  Each register field
is a centered blue header above an LCD-style hex display; each flag is
a small LCD-style box that reads ``x`` until the CPU has written that
flag, then ``0`` or ``1`` to reflect its current state.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QLabel, QGroupBox,
    QVBoxLayout, QHBoxLayout, QGridLayout,
)

from ..constants import FLAG_C, FLAG_Z, FLAG_N, FLAG_V, FLAG_I
from ..styles import C
from ..widgets.leds import LEDDisplay, FlagLight


class CPUPanel(QWidget):
    def __init__(self, cpu, parent=None):
        super().__init__(parent)
        self.cpu = cpu
        self.setWindowTitle("CPU Register Display")
        self._build()

    # ---------------------------------------------------------------- build --

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 8, 10, 8)

        # ----- Register grid (3 rows x 2 columns) ---------------------
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)

        # Row 0
        grid.addLayout(self._reg_field("Accumulator", 2,
                                       attr="acc_disp"),     0, 0)
        grid.addLayout(self._reg_field("Program Counter", 4,
                                       attr="pc_disp"),      0, 1)
        # Row 1
        grid.addLayout(self._reg_field("Instruction Reg", 2,
                                       attr="instr_disp"),   1, 0)
        grid.addLayout(self._reg_field("Index Reg", 4,
                                       attr="ix_disp"),      1, 1)
        # Row 2
        grid.addLayout(self._reg_field("Interrupt Vector", 4,
                                       attr="iv_disp"),      2, 0)
        grid.addLayout(self._reg_field("Stack Pointer", 4,
                                       attr="sp_disp"),      2, 1)

        layout.addLayout(grid)

        # ----- Status Reg group --------------------------------------
        flag_box = QGroupBox("Status Reg")
        flag_box.setAlignment(Qt.AlignHCenter)
        # Bump the group-box title font to match the larger labels inside.
        flag_box.setStyleSheet(
            "QGroupBox { font-weight: bold; font-size: 12px; }"
            "QGroupBox::title { padding: 0 6px; }"
        )
        fb_layout = QVBoxLayout(flag_box)
        fb_layout.setContentsMargins(12, 18, 12, 10)
        fb_layout.setSpacing(6)

        flag_row = QHBoxLayout()
        flag_row.setSpacing(8)
        flag_row.addStretch()

        # Display name -> CPU's internal flag key (constants module name).
        # The DIY Calculator labels overflow as "O"; internally we call it V.
        self.flags = {}
        flag_order = [
            ("I", "I"),
            ("O", "V"),
            ("N", "N"),
            ("Z", "Z"),
            ("C", "C"),
        ]
        for disp_name, cpu_key in flag_order:
            flag_row.addLayout(self._flag_field(disp_name, cpu_key))

        flag_row.addStretch()
        fb_layout.addLayout(flag_row)
        layout.addWidget(flag_box)

    # All six register displays use the same physical box size so the
    # two-column grid is symmetric and the narrower ``$XX`` registers
    # visually line up with the 16-bit ones above and below them.
    # The box is sized for 6 hex chars — two wider than the longest
    # value (``$XXXX``) so there's generous breathing room.
    _BOX_WIDTH = 6

    def _reg_field(self, label, width, attr):
        """Build a column with a blue header above a centered LCD display.

        ``width`` is the number of hex digits the register holds
        (formatting only); the visible box is always sized to fit four
        hex digits, see :data:`_BOX_WIDTH`.
        """
        col = QVBoxLayout()
        col.setSpacing(2)
        col.setContentsMargins(0, 0, 0, 0)

        hdr = QLabel(label)
        hdr.setAlignment(Qt.AlignCenter)
        hdr.setStyleSheet(
            f"color:{C['blue']}; font-weight:bold; font-size:9px; "
            "background:transparent;"
        )

        disp = LEDDisplay(width, box_width=self._BOX_WIDTH)
        disp.setAlignment(Qt.AlignCenter)

        col.addWidget(hdr)
        col.addWidget(disp, alignment=Qt.AlignCenter)
        setattr(self, attr, disp)
        return col

    def _flag_field(self, disp_name, cpu_key):
        """Build a column with a flag-letter header above an LCD box."""
        col = QVBoxLayout()
        col.setSpacing(2)
        col.setContentsMargins(0, 0, 0, 0)

        hdr = QLabel(disp_name)
        hdr.setAlignment(Qt.AlignCenter)
        hdr.setStyleSheet(
            f"color:{C['blue']}; font-weight:bold; font-size:9px; "
            "background:transparent;"
        )

        fl = FlagLight(disp_name)
        col.addWidget(hdr)
        col.addWidget(fl, alignment=Qt.AlignCenter)
        self.flags[cpu_key] = fl
        return col

    # ---------------------------------------------------------------- refresh

    def refresh(self):
        self.acc_disp.setValue(self.cpu.acc)
        self.pc_disp.setValue(self.cpu.pc)
        # SP is now a full 16-bit register — display it directly.
        self.sp_disp.setValue(self.cpu.sp)
        self.ix_disp.setValue(self.cpu.ix)
        self.instr_disp.setValue(self.cpu.instr)

        # Interrupt vector: held in cpu._intr_vector (set by BLDIV instruction).
        self.iv_disp.setValue(getattr(self.cpu, "_intr_vector", 0xFFFE))

        # `flags_touched` is a bitmask of flags the CPU has ever written.
        # Flags that have never been written are rendered as "x" so the
        # user can tell uninitialised flags apart from cleared ones.
        f = self.cpu.flags
        t = getattr(self.cpu, "flags_touched", 0xFF)
        for cpu_key, mask in (
            ("I", FLAG_I), ("V", FLAG_V), ("N", FLAG_N),
            ("Z", FLAG_Z), ("C", FLAG_C),
        ):
            if t & mask:
                self.flags[cpu_key].setOn(f & mask)
            else:
                self.flags[cpu_key].setUnknown()
