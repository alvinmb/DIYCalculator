"""
QT_compile.py  –  DIY Calculator Assembler GUI (PyQt5)

Place in the same folder as:
    das.py           David's Assembler engine (Python port)
    compiler_core.py Assembler wrapper / result types

Run:
    python QT_compile.py
"""

import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QFileDialog, QMessageBox, QLabel, QSplitter,
)

from compiler_core import Compiler


class CompilerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DIY Calculator Assembler")
        self.resize(900, 600)

        self.compiler     = Compiler()
        self.current_path: Path | None = None

        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # ── Toolbar ──────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        main_layout.addLayout(toolbar)

        self.open_button    = QPushButton("Open")
        self.save_button    = QPushButton("Save")
        self.save_as_button = QPushButton("Save As")
        self.compile_button = QPushButton("Compile")

        toolbar.addWidget(self.open_button)
        toolbar.addWidget(self.save_button)
        toolbar.addWidget(self.save_as_button)
        toolbar.addStretch(1)
        toolbar.addWidget(self.compile_button)

        # ── Editor / Messages splitter ───────────────────────────────────
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter, 1)

        mono = self.font()
        mono.setFamily("Courier New")
        mono.setPointSize(10)

        ed_box = QWidget()
        ed_lay = QVBoxLayout(ed_box)
        ed_lay.setContentsMargins(0, 0, 0, 0)
        ed_lay.addWidget(QLabel("Source  (.asm)"))
        self.editor = QTextEdit()
        self.editor.setFont(mono)
        self.editor.setTabStopDistance(4 * self.editor.fontMetrics().horizontalAdvance(" "))
        ed_lay.addWidget(self.editor, 1)

        msg_box = QWidget()
        msg_lay = QVBoxLayout(msg_box)
        msg_lay.setContentsMargins(0, 0, 0, 0)
        msg_lay.addWidget(QLabel("Messages"))
        self.messages = QTextEdit()
        self.messages.setFont(mono)
        self.messages.setReadOnly(True)
        msg_lay.addWidget(self.messages, 1)

        splitter.addWidget(ed_box)
        splitter.addWidget(msg_box)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        # ── Signals ───────────────────────────────────────────────────────
        self.open_button.clicked.connect(self.on_open)
        self.save_button.clicked.connect(self.on_save)
        self.save_as_button.clicked.connect(self.on_save_as)
        self.compile_button.clicked.connect(self.on_compile)

    # ── Source file I/O ───────────────────────────────────────────────────

    def on_open(self):
        dlg = QFileDialog(self, "Open Assembly Source")
        dlg.setAcceptMode(QFileDialog.AcceptOpen)
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setNameFilters(["Assembly Files (*.asm)", "All Files (*)"])
        dlg.selectNameFilter("Assembly Files (*.asm)")
        dlg.setDefaultSuffix("asm")
        if self.current_path:
            dlg.setDirectory(str(self.current_path.parent))
        if dlg.exec_() != QFileDialog.Accepted:
            return
        path = Path(dlg.selectedFiles()[0])
        try:
            self.editor.setPlainText(path.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:
            QMessageBox.critical(self, "Open failed", str(exc))
            return
        self.current_path = path
        self.setWindowTitle(f"DIY Calculator Assembler  –  {path.name}")
        self.statusBar().showMessage(f"Opened: {path}", 4000)

    def on_save(self):
        if self.current_path is None:
            self.on_save_as()
        else:
            self._write_source(self.current_path)

    def on_save_as(self):
        dlg = QFileDialog(self, "Save Assembly Source")
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        dlg.setNameFilters(["Assembly Files (*.asm)", "All Files (*)"])
        dlg.selectNameFilter("Assembly Files (*.asm)")
        dlg.setDefaultSuffix("asm")
        if self.current_path:
            dlg.setDirectory(str(self.current_path.parent))
            dlg.selectFile(self.current_path.with_suffix(".asm").name)
        else:
            dlg.selectFile("untitled.asm")
        if dlg.exec_() != QFileDialog.Accepted:
            return
        path = Path(dlg.selectedFiles()[0])
        if path.suffix.lower() != ".asm":
            path = path.with_suffix(".asm")
        self._write_source(path)
        self.current_path = path
        self.setWindowTitle(f"DIY Calculator Assembler  –  {path.name}")

    def _write_source(self, path: Path):
        """Save the editor text as a UTF-8 text file (.asm)."""
        try:
            path.write_text(self.editor.toPlainText(), encoding="utf-8")
            self.statusBar().showMessage(f"Saved: {path}", 4000)
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", str(exc))

    # ── Compile → .ram ────────────────────────────────────────────────────

    def on_compile(self):
        self.messages.clear()
        result = self.compiler.compile_source(self.editor.toPlainText())

        for msg in result.messages:
            self.messages.append(msg)

        if result.success and result.bytecode:
            self._write_ram(result.bytecode)
        else:
            self.statusBar().showMessage("Compilation failed", 4000)

    def _write_ram(self, ram_bytes: bytes):
        """
        Write the assembled RAM image as a binary .ram file.
        Defaults to <source_stem>.ram alongside the open .asm file.
        Always uses write_bytes() so the file is binary, never text.
        """
        if self.current_path is not None:
            out_path = self.current_path.with_suffix(".ram")
        else:
            dlg = QFileDialog(self, "Save RAM Image")
            dlg.setAcceptMode(QFileDialog.AcceptSave)
            dlg.setNameFilters(["RAM Image (*.ram)", "All Files (*)"])
            dlg.selectNameFilter("RAM Image (*.ram)")
            dlg.setDefaultSuffix("ram")
            dlg.selectFile("untitled.ram")
            if dlg.exec_() != QFileDialog.Accepted:
                self.messages.append("RAM image not saved (cancelled).")
                return
            out_path = Path(dlg.selectedFiles()[0])
            if out_path.suffix.lower() != ".ram":
                out_path = out_path.with_suffix(".ram")

        try:
            # write_bytes writes raw binary – never call write_text here
            out_path.write_bytes(ram_bytes)
            self.messages.append(f"RAM image written to: {out_path}")
            self.statusBar().showMessage(f"Compiled  →  {out_path.name}", 4000)
        except Exception as exc:
            self.messages.append(f"Failed to write RAM image: {exc}")
            self.statusBar().showMessage("Write failed", 4000)


# ── Entry point ───────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    win = CompilerWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
