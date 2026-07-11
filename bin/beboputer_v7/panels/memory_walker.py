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

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
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

    # "Walk 64K" auto-paging: page size (rows per page == table row count)
    # and delay between pages, in milliseconds.
    WALK_PAGE_SIZE = 256
    WALK_INTERVAL_MS = 400

    # Breakpoints set by default on every fresh Memory Walker (app start).
    # $0000 catches the common "JMP [$0000]" NOP-sled idiom used by
    # lab2a and friends as an old-fashioned HALT substitute, so Run
    # stops there instead of free-running through it forever.
    DEFAULT_BREAKPOINTS = {0x0000}

    def __init__(self, cpu, parent=None):
        super().__init__(parent)
        self.cpu = cpu
        self.setWindowTitle("Memory Walker")
        self._base = 0
        self._breakpoints = set(self.DEFAULT_BREAKPOINTS)   # absolute addresses with BP set
        self._user_nav = False       # True when user has manually navigated with GO

        # Continuous 64K auto-page ("Walk") state
        self._walking = False
        self._walk_timer = QTimer(self)
        self._walk_timer.timeout.connect(self._walk_step)

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
        # setFont() alone doesn't render bold here: the app-wide QSS in
        # styles.py sets font-family/font-size on QPushButton, and once a
        # stylesheet touches any font property Qt stops merging in the
        # widget's QFont for the rest (font-weight silently resets to
        # normal). An explicit "font-weight: bold;" rule wins instead.
        self.go_btn.setStyleSheet("font-weight: bold;")
        self.go_btn.setToolTip(
            "Jump the view to the address typed in the box, and lock it "
            "there until you step or click Go to PC."
        )
        self.go_btn.clicked.connect(self._go)
        nav.addWidget(self.go_btn)

        self.goto_pc_btn = QPushButton("Go to PC")
        self.goto_pc_btn.setToolTip(
            "Jump the view back to wherever the Program Counter "
            "currently is, and resume following it."
        )
        self.goto_pc_btn.setStyleSheet("font-weight: bold;")
        self.goto_pc_btn.clicked.connect(self._goto_pc)
        nav.addWidget(self.goto_pc_btn)

        nav.addStretch()

        self.run_bp_btn = QPushButton("RUN to BP")
        self.run_bp_btn.setToolTip("Run until a breakpoint, HALT, or step limit.")
        self.run_bp_btn.setStyleSheet(
            # NOTE: properties MUST be wrapped in an explicit "QPushButton
            # { ... }" selector block here, NOT written as bare/unwrapped
            # declarations. A bare declaration list mixed with a trailing
            # "QToolTip { ... }" rule in the same setStyleSheet() string is
            # ambiguous Qt CSS and silently fails to apply the QToolTip
            # override -- which is why this exact button kept reverting to
            # red-on-grey tooltips across multiple fix attempts while the
            # calculator/DIY buttons (which already used this fully-wrapped
            # QPushButton{}/QToolTip{} format) held their fix correctly.
            f"QPushButton {{"
            f"background-color:{C['btn_bg']}; color:{C['red']}; "
            f"border:1px solid {C['btn_bdr']}; "
            f"border-top-color:{C['border_lt']}; border-left-color:{C['border_lt']}; "
            "border-radius:2px; padding:3px 8px; font-weight:bold;"
            "}"
            "QToolTip { background-color: #ffffcc; color: #000000; "
            "border: 1px solid #808080; padding: 2px 4px; }"
        )
        self.run_bp_btn.clicked.connect(self.run_to_breakpoint)
        nav.addWidget(self.run_bp_btn)

        self.clear_bp_btn = QPushButton("Clear BPs")
        self.clear_bp_btn.setToolTip("Remove all breakpoints")
        self.clear_bp_btn.setStyleSheet("font-weight: bold;")
        self.clear_bp_btn.clicked.connect(self._clear_all_breakpoints)
        nav.addWidget(self.clear_bp_btn)

        self.walk_btn = QPushButton("Walk 64K")
        self.walk_btn.setToolTip(
            "Continuously page through the full 64K address space, "
            "one 256-byte page at a time, wrapping back to $0000."
        )
        self.walk_btn.setStyleSheet("font-weight: bold;")
        self.walk_btn.setCheckable(True)
        self.walk_btn.clicked.connect(self._toggle_walk)
        nav.addWidget(self.walk_btn)

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
        # Row count must match the 256-row visible window that
        # _refresh() populates (see VISIBLE_ROWS in highlight_pc) —
        # with more rows than _refresh() ever fills, the extra rows
        # stayed permanently blank (no address, no "$XX"), which
        # looked like the table "stopped displaying" partway down.
        self.table = QTableWidget(256, 4)
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
            self._stop_walk()        # manual nav overrides auto-paging
            self._base = addr
            self._user_nav = True    # lock the view here until user steps
            self._refresh()
            self.table.scrollToTop()
        except ValueError:
            pass

    def _goto_pc(self):
        """Snap the view back to the current PC and resume PC-following.

        Manual GO navigation (and Walk 64K) deliberately leave the ▶
        marker off-screen when you've navigated elsewhere -- that's by
        design, so you can inspect code without the view fighting you.
        This button is the escape hatch: click it any time to find out
        where execution actually is right now.
        """
        self._stop_walk()
        self._user_nav = False
        self.highlight_pc(self.cpu.pc)
        self._set_status(f"Jumped to PC=${self.cpu.pc:04X}", C['amber'])

    # ------------------------------------------------------- walk 64K ----

    def _toggle_walk(self, checked):
        if checked:
            self._start_walk()
        else:
            self._stop_walk()

    def _start_walk(self):
        self._walking = True
        self._user_nav = True   # auto-paging owns the view; PC-follow is suspended
        self.walk_btn.setChecked(True)
        self.walk_btn.setText("Stop Walk")
        self._set_status("Walking 64K memory space...", C['amber'])
        self._walk_timer.start(self.WALK_INTERVAL_MS)

    def _stop_walk(self):
        if self._walking:
            self._walk_timer.stop()
            self._walking = False
            self.walk_btn.setChecked(False)
            self.walk_btn.setText("Walk 64K")
            self._set_status(f"Walk stopped at ${self._base:04X}", C['grey'])

    def _walk_step(self):
        # Advance one full page and wrap around at the top of the 64K
        # address space, so the view continuously cycles $0000..$FFFF.
        self._base = (self._base + self.WALK_PAGE_SIZE) % 0x10000
        self.addr_edit.setText(f"{self._base:04X}")
        self._refresh()
        self.table.scrollToTop()

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

            # DATA column — undefined (never-written) RAM shows as "XX",
            # matching real hardware where power-on RAM contents are
            # indeterminate until the program writes to them.
            touched = self.cpu.ram_touched[addr]
            data_item = QTableWidgetItem(f"{b:02X}" if touched else "XX")
            data_item.setTextAlignment(Qt.AlignCenter)
            if not touched:
                data_item.setForeground(QBrush(QColor(C['grey'])))
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

        self._stop_walk()
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
            self.cpu.ram_touched[addr] = 1
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

        self._stop_walk()
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

    def closeEvent(self, event):
        self._walk_timer.stop()
        super().closeEvent(event)
