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

"""
Memory Walker — scrollable memory dump with single-step + breakpoints.

Features:
  - BP column: click a row to toggle a filled red circle ●  (second
    click removes it).  Breakpoints are absolute RAM addresses stored
    in ``self._breakpoints`` (a ``set``).
  - STEP column: click any cell in column 1 to execute exactly one
    CPU instruction, then refresh the view and emit
    ``step_executed(mnemonic)`` so :class:`BebopMain` can update other
    panels.
  - ``run_to_breakpoint()`` steps the CPU until PC hits any address in
    ``_breakpoints``, the CPU HALTs, or a safety limit is reached.
    Emits ``bp_hit`` so the main window can refresh all sub-windows.
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QApplication,
)

from ..constants import RUN_LIMIT
from ..styles import C


class MemoryWalker(QWidget):
    # Emitted when run_to_breakpoint stops; arg = reason string
    bp_hit = pyqtSignal(str)
    # Emitted after a single STEP; arg = mnemonic string returned by cpu.step()
    step_executed = pyqtSignal(str)

    def __init__(self, cpu, parent=None):
        super().__init__(parent)
        self.cpu = cpu
        self.setWindowTitle("Memory Walker")
        self._base = 0
        self._breakpoints = set()   # absolute addresses with BP set
        self._user_nav = False       # True when user has manually navigated with GO
        self._build()

    # ---------------------------------------------------------------- build --

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        # Navigation bar
        nav = QHBoxLayout()
        nav.addWidget(QLabel("Address:"))

        self.addr_edit = QLineEdit("0000")
        self.addr_edit.setStyleSheet(
            "font-family: 'Courier New'; font-size: 14pt; font-weight: bold;"
        )
        self.addr_edit.setFixedWidth(95)
        self.addr_edit.setMaxLength(5)
        nav.addWidget(self.addr_edit)

        self.go_btn = QPushButton("GO")
        self.go_btn.setFixedWidth(65)
        self.go_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.go_btn.clicked.connect(self._go)
        nav.addWidget(self.go_btn)

        nav.addStretch()

        self.run_bp_btn = QPushButton("RUN to BP")
        self.run_bp_btn.setToolTip("Run until a breakpoint, HALT, or step limit.")
        self.run_bp_btn.setStyleSheet(
            f"background-color:{C['btn_bg']}; color:{C['red']}; "
            f"border:1px solid {C['btn_bdr']}; "
            f"border-top-color:{C['border_lt']}; border-left-color:{C['border_lt']}; "
            "border-radius:2px; padding:3px 8px; font-weight:bold;"
        )
        self.run_bp_btn.clicked.connect(self.run_to_breakpoint)
        nav.addWidget(self.run_bp_btn)

        self.clear_bp_btn = QPushButton("Clear BPs")
        self.clear_bp_btn.setToolTip("Remove all breakpoints")
        self.clear_bp_btn.clicked.connect(self._clear_all_breakpoints)
        nav.addWidget(self.clear_bp_btn)

        layout.addLayout(nav)

        # Status bar
        self.status_lbl = QLabel(
            "Click STEP column to single-step  |  Click BP column to toggle breakpoint"
        )
        self.status_lbl.setStyleSheet(
            f"color:{C['grey']}; font-size:10px; font-style:italic;"
        )
        layout.addWidget(self.status_lbl)

        # Memory table  (BP | STEP | ADDRESS | DATA)
        self.table = QTableWidget(500, 4)
        self.table.setHorizontalHeaderLabels(["BP", "STEP", "ADDRESS", "DATA"])
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 180)
        self.table.verticalHeader().setDefaultSectionSize(20)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.table.setFont(QFont("Courier New", 14, QFont.Bold))
        self.table.cellClicked.connect(self._cell_clicked)
        self.table.cellChanged.connect(self._cell_changed)

        layout.addWidget(self.table)
        self._refresh()

    # --------------------------------------------------------- navigation --

    def _go(self):
        try:
            addr = int(self.addr_edit.text().strip(), 16) & 0xFFFF
            self._base = addr
            self._user_nav = True    # lock the view here until user steps
            self._refresh()
            self.table.scrollToTop()
        except ValueError:
            pass

    def _refresh(self):
        self.table.blockSignals(True)
        pc = self.cpu.pc

        for row in range(256):
            addr = (self._base + row) & 0xFFFF
            b    = self.cpu.ram[addr]
            is_pc = (addr == pc)

            # BP column
            bp_item = QTableWidgetItem()
            bp_item.setTextAlignment(Qt.AlignCenter)
            bp_item.setFlags(Qt.ItemIsEnabled)
            if addr in self._breakpoints:
                bp_item.setText("●")
                bp_item.setForeground(QBrush(QColor(C['red'])))
                bp_item.setFont(QFont("Courier New", 14, QFont.Bold))
            self.table.setItem(row, 0, bp_item)

            # STEP column — show ▶ at the PC row, faint dot elsewhere
            if is_pc:
                step_item = QTableWidgetItem("▶")
                step_item.setForeground(QBrush(QColor(C['amber'])))
                step_item.setFont(QFont("Courier New", 14, QFont.Bold))
            else:
                step_item = QTableWidgetItem("·")
                step_item.setForeground(QBrush(QColor(C['grey'])))
                step_item.setFont(QFont("Courier New", 14, QFont.Bold))
            step_item.setTextAlignment(Qt.AlignCenter)
            step_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 1, step_item)

            # ADDRESS column
            addr_item = QTableWidgetItem(f"${addr:04X}")
            addr_item.setFlags(Qt.ItemIsEnabled)
            addr_fg = QColor(C['green']) if is_pc else QColor(C['green_mid'])
            addr_item.setForeground(QBrush(addr_fg))
            if is_pc:
                addr_item.setFont(QFont("Courier New", 14, QFont.Bold))
            self.table.setItem(row, 2, addr_item)

            # DATA column
            data_item = QTableWidgetItem(f"{b:02X}")
            data_item.setTextAlignment(Qt.AlignCenter)
            if is_pc:
                data_item.setForeground(QBrush(QColor(C['amber'])))
                data_item.setFont(QFont("Courier New", 14, QFont.Bold))
            self.table.setItem(row, 3, data_item)

        self.table.blockSignals(False)

    # ---------------------------------------------------------- clicking --

    def _cell_clicked(self, row, col):
        if col == 0:
            self._toggle_bp(row)
        elif col == 1:
            self._do_step()

    # -------------------------------------------------------- breakpoints --

    def _toggle_bp(self, row):
        addr = (self._base + row) & 0xFFFF
        if addr in self._breakpoints:
            self._breakpoints.discard(addr)
            self._set_status(f"BP removed at ${addr:04X}", C['grey'])
        else:
            self._breakpoints.add(addr)
            self._set_status(f"BP set at ${addr:04X}", C['red'])
        self._refresh_bp_cell(row, addr)

    def _refresh_bp_cell(self, row, addr):
        self.table.blockSignals(True)
        bp_item = self.table.item(row, 0)
        if bp_item is None:
            bp_item = QTableWidgetItem()
            bp_item.setTextAlignment(Qt.AlignCenter)
            bp_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 0, bp_item)
        if addr in self._breakpoints:
            bp_item.setText("●")
            bp_item.setForeground(QBrush(QColor(C['red'])))
            bp_item.setFont(QFont("Courier New", 14, QFont.Bold))
        else:
            bp_item.setText("")
        self.table.blockSignals(False)

    def _clear_all_breakpoints(self):
        self._breakpoints.clear()
        self._set_status("All breakpoints cleared.", C['grey'])
        self._refresh()

    # --------------------------------------------------------- single step --

    def _do_step(self):
        if self.cpu.halted:
            self._set_status("CPU is HALTed — Reset before stepping.", C['red'])
            return

        self._user_nav = False       # resume PC-following on explicit step
        mnemonic = self.cpu.step()
        self.highlight_pc(self.cpu.pc)

        if self.cpu.halted:
            self._set_status(f"HALT executed — PC=${self.cpu.pc:04X}", C['red'])
        else:
            self._set_status(
                f"Stepped  PC=${self.cpu.pc:04X}  {mnemonic}  ACC=${self.cpu.acc:02X}",
                C['amber']
            )

        self.step_executed.emit(mnemonic)

    # -------------------------------------------------------- DATA editing --

    def _cell_changed(self, row, col):
        if col != 3:
            return
        addr = (self._base + row) & 0xFFFF
        item = self.table.item(row, col)
        if item is None:
            return
        try:
            self.cpu.ram[addr] = int(item.text(), 16) & 0xFF
        except Exception:
            pass

    # ------------------------------------------------------- run to BP ----

    def run_to_breakpoint(self):
        if not self._breakpoints:
            self._set_status("No breakpoints set — click a BP cell first.", C['red'])
            return
        if self.cpu.halted:
            self._set_status("CPU is HALTed — Reset before running.", C['red'])
            return

        self._set_status("Running...", C['grey'])
        QApplication.processEvents()

        batch = 500
        executed = 0

        while executed < RUN_LIMIT:
            for _ in range(batch):
                if self.cpu.halted:
                    break
                self.cpu.step()
                executed += 1
                if self.cpu.pc in self._breakpoints:
                    reason = f"BP hit at ${self.cpu.pc:04X} after {executed} steps"
                    self._set_status(reason, C['red'])
                    self.highlight_pc(self.cpu.pc)
                    self.bp_hit.emit(reason)
                    return

            if self.cpu.halted:
                reason = f"HALT at ${self.cpu.pc:04X} after {executed} steps"
                self._set_status(reason, C['red'])
                self.highlight_pc(self.cpu.pc)
                self.bp_hit.emit(reason)
                return

            QApplication.processEvents()

        reason = f"Step limit ({RUN_LIMIT:,}) reached at ${self.cpu.pc:04X}"
        self._set_status(reason, C['red'])
        self.highlight_pc(self.cpu.pc)
        self.bp_hit.emit(reason)

    # --------------------------------------------------------- PC tracking --

    def highlight_pc(self, pc):
        """Move the ▶ step marker to the row matching the new PC.

        While PC is inside the 256-row window the marker walks down
        the table without disturbing the scroll position.

        If the user has manually navigated with GO (``_user_nav=True``)
        the view is NOT re-anchored — their chosen address is respected
        even if PC is off-screen.  The flag is cleared once the user
        steps from inside the Memory Walker (via _do_step), at which
        point normal PC-following resumes.

        If ``_user_nav`` is False (normal PC-following mode) and PC
        leaves the visible window, we re-anchor ``_base`` so PC appears
        near the top with a small lead-in for context.
        """
        pc &= 0xFFFF
        offset = (pc - self._base) & 0xFFFF
        VISIBLE_ROWS = 256

        if offset >= VISIBLE_ROWS:
            if self._user_nav:
                # User navigated here intentionally — just refresh in
                # place; the ▶ marker won't appear but that's expected.
                self._refresh()
                return
            # Normal PC-following: re-anchor near PC.
            LEAD_IN = 4
            self._base = (pc - LEAD_IN) & 0xFFFF
            self.addr_edit.setText(f"{self._base:04X}")
            offset = LEAD_IN

        self._refresh()
        item = self.table.item(offset, 2)
        if item:
            self.table.scrollToItem(item)

    # ---------------------------------------------------------------- util --

    def _set_status(self, text, colour):
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(
            f"color:{colour}; font-size:10px; font-style:italic;"
        )
