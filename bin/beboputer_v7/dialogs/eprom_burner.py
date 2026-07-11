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

"""EPROM Burner dialog — dump / load RAM ranges to/from .rom files."""

import os
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QLabel, QPushButton, QLineEdit, QGroupBox,
    QVBoxLayout, QHBoxLayout, QFormLayout,
    QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem,
)

from ..styles import C

# ── Cross-platform file-dialog default directories ──────────────────────────
# default_open_dir()/default_save_dir() (see ../paths.py) point at Data/
# WorkInProgress when running from source, and at a single writable
# ~/Documents/PY-DIYCALCULATOR workspace (seeded with the sample files) in
# packaged builds, since the app's install folder is not reliably writable
# by a non-admin user there (Program Files, Pi's root-owned /usr/share, …).
try:
    from ..paths import default_open_dir as _default_open_dir, default_save_dir as _default_save_dir
except Exception:
    def _default_open_dir() -> str:
        return str(Path.home())

    def _default_save_dir() -> str:
        d = Path.home() / 'beboputer'
        d.mkdir(exist_ok=True)
        return str(d)


class EpromBurner(QDialog):
    # Emitted after a successful Load ROM / Swap ROMs so the main window
    # can refresh panels (Memory Walker in particular) that hold their
    # own view of cpu.ram and won't otherwise notice bytes changed out
    # from under them.
    ram_changed = pyqtSignal()

    def __init__(self, cpu, parent=None):
        super().__init__(parent)
        self.cpu = cpu
        self.setWindowTitle("EPROM Burner")
        self.setFixedSize(525, 375)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(12, 12, 12, 12)

        _lbl_style = (
            f"color: {C['blue']}; font-weight: bold; font-size: 10px;"
        )
        _field_style = (
            f"background: {C['lcd_bg']}; color: #000; "
            f"border: 2px inset {C['btn_bdr']}; "
            "font-family: 'Courier New'; font-weight: bold; font-size: 11pt; "
            "padding: 1px 5px; min-height: 22px;"
        )

        def _lbl(text):
            l = QLabel(text)
            l.setStyleSheet(_lbl_style)
            return l

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        self.file_edit  = QLineEdit()
        self.start_edit = QLineEdit("0000")
        self.end_edit   = QLineEdit("00FF")
        for w in (self.file_edit, self.start_edit, self.end_edit):
            w.setStyleSheet(_field_style)
        form.addRow(_lbl("File Name:"),      self.file_edit)
        form.addRow(_lbl("Start Address $"), self.start_edit)
        form.addRow(_lbl("End Address $"),   self.end_edit)
        root.addLayout(form)

        # Available EPROMs list
        avail_box = QGroupBox("Available System EPROMs")
        avail_layout = QVBoxLayout(avail_box)
        self.eprom_list = QTableWidget(0, 2)
        self.eprom_list.setHorizontalHeaderLabels(["File", "Size"])
        self.eprom_list.horizontalHeader().setStretchLastSection(True)
        self.eprom_list.setFixedHeight(100)
        avail_layout.addWidget(self.eprom_list)
        root.addWidget(avail_box)

        # Buttons
        btn_row = QHBoxLayout()
        for lbl, slot in [("&Browse...", self._browse),
                          ("&Burn ROM",  self._burn),
                          ("&Load ROM",  self._load_rom),
                          ("&Swap ROMs", self._swap),
                          ("Cancel",     self.reject)]:
            b = QPushButton(lbl); b.clicked.connect(slot); btn_row.addWidget(b)
        root.addLayout(btn_row)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(f"color:{C['green_mid']}; font-size:10px;")
        root.addWidget(self.status_lbl)

    def _browse(self):
        dlg = QFileDialog(self, "Select ROM file")
        dlg.setOption(QFileDialog.DontUseNativeDialog)
        dlg.setAcceptMode(QFileDialog.AcceptOpen)
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setNameFilters(["ROM Files (*.rom *.bin)", "All Files (*)"])
        dlg.setDirectory(_default_open_dir())
        if dlg.exec_() != QFileDialog.Accepted:
            return
        path = dlg.selectedFiles()[0]
        if path:
            self.file_edit.setText(path)
            row = self.eprom_list.rowCount()
            self.eprom_list.insertRow(row)
            self.eprom_list.setItem(row, 0, QTableWidgetItem(os.path.basename(path)))
            try:
                self.eprom_list.setItem(row, 1, QTableWidgetItem(f"{os.path.getsize(path)} B"))
            except OSError:
                pass

    def _burn(self):
        """Dump a RAM range to a file (simulated EPROM burn)."""
        path = self.file_edit.text()
        if not path:
            dlg = QFileDialog(self, "Burn to File")
            dlg.setOption(QFileDialog.DontUseNativeDialog)
            dlg.setAcceptMode(QFileDialog.AcceptSave)
            dlg.setNameFilters(["ROM Files (*.rom)", "All Files (*)"])
            dlg.setDefaultSuffix("rom")
            dlg.setDirectory(_default_save_dir())
            if dlg.exec_() != QFileDialog.Accepted:
                return
            path = dlg.selectedFiles()[0]
            if not path:
                return
            self.file_edit.setText(path)
        try:
            start = int(self.start_edit.text(), 16) & 0xFFFF
            end   = int(self.end_edit.text(),   16) & 0xFFFF
            if end < start:
                end = start
            data = bytes(self.cpu.ram[start:end+1])
            with open(path, "wb") as f:
                f.write(data)
            self.status_lbl.setText(f"Burned ${start:04X}–${end:04X} → {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Burn Error", str(e))

    def _load_rom(self):
        """Load a file into RAM at the start address."""
        path = self.file_edit.text()
        if not path:
            dlg = QFileDialog(self, "Load ROM")
            dlg.setOption(QFileDialog.DontUseNativeDialog)
            dlg.setAcceptMode(QFileDialog.AcceptOpen)
            dlg.setFileMode(QFileDialog.ExistingFile)
            dlg.setNameFilters(["ROM Files (*.rom *.bin)", "All Files (*)"])
            dlg.setDirectory(_default_open_dir())
            if dlg.exec_() != QFileDialog.Accepted:
                return
            path = dlg.selectedFiles()[0]
            if not path:
                return
            self.file_edit.setText(path)
        try:
            start = int(self.start_edit.text(), 16) & 0xFFFF
            with open(path, "rb") as f:
                data = f.read()
            for i, b in enumerate(data):
                if start + i >= 0x10000:
                    break
                self.cpu.ram[start + i] = b
                # Mark loaded bytes as known — otherwise Memory Walker
                # keeps showing them as undefined ($XX) even though a
                # real file's contents now live there.
                self.cpu.ram_touched[start + i] = 1
            self.status_lbl.setText(f"Loaded {len(data)}B at ${start:04X} from {os.path.basename(path)}")
            self.ram_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))

    def _swap(self):
        """Swap two ROM ranges."""
        try:
            start = int(self.start_edit.text(), 16) & 0xFFFF
            end   = int(self.end_edit.text(),   16) & 0xFFFF
            mid   = (start + end) // 2 + 1
            for i in range(end - mid + 1):
                a, b = self.cpu.ram[start+i], self.cpu.ram[mid+i]
                self.cpu.ram[start+i], self.cpu.ram[mid+i] = b, a
                ta, tb = self.cpu.ram_touched[start+i], self.cpu.ram_touched[mid+i]
                self.cpu.ram_touched[start+i], self.cpu.ram_touched[mid+i] = tb, ta
            self.status_lbl.setText(f"Swapped ${start:04X}–${mid-1:04X} ↔ ${mid:04X}–${end:04X}")
            self.ram_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Swap Error", str(e))
