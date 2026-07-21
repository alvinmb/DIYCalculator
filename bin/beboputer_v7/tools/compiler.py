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
CompilerWindow — DIY Calculator Assembler GUI.

Architecture
------------
AssemblerRunner   — pure logic: compile source, write RAM image, load into CPU.
                    No Qt dependency; independently testable.
CompilerWindow    — QMainWindow shell that owns the editor widget and delegates
                    all compile/load work to an AssemblerRunner instance.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QTextCursor, QFont
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPageSetupDialog
from PyQt5.QtWidgets import (
    QAction, QFontDialog, QInputDialog,
    QMainWindow, QWidget, QLabel, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QSplitter,
    QFileDialog, QMessageBox, QStatusBar,
)

# compiler_core + das.py live two levels up in bin/
_BIN_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BIN_DIR) not in sys.path:
    sys.path.insert(0, str(_BIN_DIR))

# ── Cross-platform file-dialog directories ───────────────────────────────────
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
        user_dir = Path.home() / 'beboputer'
        user_dir.mkdir(exist_ok=True)
        return str(user_dir)

try:
    from compiler_core import Compiler as _AsmCompiler
    _COMPILER_AVAILABLE = True
    _COMPILER_IMPORT_ERROR = None
except Exception as _exc:
    _AsmCompiler = None
    _COMPILER_AVAILABLE = False
    _COMPILER_IMPORT_ERROR = str(_exc)


# ─────────────────────────────────────────────────────────────────────────────
# AssemblerRunner — pure logic, no Qt
# ─────────────────────────────────────────────────────────────────────────────

class AssemblerRunner:
    """Compile assembly source, write RAM images, and load into a CPU.

    This class holds no Qt state and can be used (and tested) without a
    display.  The :class:`CompilerWindow` owns one instance and delegates
    all compile/load operations to it.
    """

    LOAD_ADDR = 0x4000
    RAM_SIZE  = 0x10000

    def __init__(self):
        self._compiler = _AsmCompiler() if _COMPILER_AVAILABLE else None
        self.available = _COMPILER_AVAILABLE
        self.import_error = _COMPILER_IMPORT_ERROR

    # ------------------------------------------------------------------

    def compile(self, source: str):
        """Assemble *source* and return the :class:`compiler_core.CompileResult`.

        Returns ``None`` if the back-end is not available.
        """
        if self._compiler is None:
            return None
        return self._compiler.compile_source(source)

    def generate_listing(self, source: str, source_path=None):
        """Assemble *source* and return the :class:`compiler_core.ListingResult`
        containing the formatted .lst text. Returns ``None`` if the
        back-end is not available.
        """
        if self._compiler is None:
            return None
        return self._compiler.generate_listing(source, source_path=source_path)

    def build_image(self, bytecode: bytes) -> bytes:
        """Return the raw assembled *bytecode*, trimmed to fit in RAM.

        Previously this padded the bytecode out to a full 64KB image
        starting at LOAD_ADDR. That made every compiled .ram file a
        65536-byte blob, which in turn made _load_file() treat the
        *entire* file as "known" -- Memory Walker showed $00 for every
        address the program never touched, instead of the undefined
        placeholder ($XX). A compact file (just the real bytes) lets
        _load_file()'s existing chunked-copy path mark only the actual
        program bytes as touched, which is what we want.
        """
        max_bytes = self.RAM_SIZE - self.LOAD_ADDR
        return bytes(bytecode[:max_bytes])

    def write_ram(self, bytecode: bytes, out_path: Path) -> None:
        """Write the compact assembled bytecode to *out_path* (.ram file).

        The file holds only the real program bytes (loaded at LOAD_ADDR
        on read-back) -- not a padded 64KB image. See build_image().
        """
        out_path.write_bytes(self.build_image(bytecode))

    def load_into_cpu(self, bytecode: bytes, cpu) -> int:
        """Load *bytecode* into *cpu* RAM at LOAD_ADDR.

        Writes in-place so MemoryWalker and other holders of cpu.ram keep
        their reference to the same bytearray object.
        Returns the number of bytes loaded.
        """
        max_bytes = cpu.RAM_SIZE - self.LOAD_ADDR
        data = bytecode[:max_bytes]
        cpu.ram[self.LOAD_ADDR : self.LOAD_ADDR + len(data)] = data
        # Mark only the actual program bytes as known -- NOT the whole
        # $4000-$FFFF range. Previously this zeroed and marked the
        # entire remaining RAM as "touched", so Memory Walker showed
        # $00 everywhere past the program instead of the undefined
        # placeholder ($XX). Same bookkeeping as _load_file()/
        # EpromBurner._load_rom(), which only mark the bytes they
        # actually supply.
        if hasattr(cpu, "ram_touched"):
            cpu.ram_touched[self.LOAD_ADDR : self.LOAD_ADDR + len(data)] = \
                b"\x01" * len(data)
        return len(data)


# ─────────────────────────────────────────────────────────────────────────────
# CompilerWindow — Qt UI shell
# ─────────────────────────────────────────────────────────────────────────────

class CompilerWindow(QMainWindow):
    """Assembler / Editor window.  All compile logic lives in AssemblerRunner."""

    def __init__(self, parent=None, host_main=None):
        super().__init__(parent)
        self.setWindowTitle("Assembler / Editor")
        self.resize(900, 600)

        self._host    = host_main           # BebopMain | None
        self._runner  = AssemblerRunner()
        self.current_path: Path | None = None
        self._find_query   = ""
        self._printer      = None
        self._last_bytecode: bytes | None = None

        self._build_ui()
        self._build_menu()

        if not self._runner.available:
            self.messages.append(
                "WARNING: compiler_core / das.py not found.\n"
                f"Import error: {self._runner.import_error}"
            )
            self.compile_button.setEnabled(False)

        self.setStatusBar(QStatusBar())

    # ---------------------------------------------------------------- UI ----

    def _build_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Toolbar row
        toolbar = QHBoxLayout()
        main_layout.addLayout(toolbar)

        self.compile_button       = QPushButton("Assemble")
        self.load_into_cpu_button = QPushButton("Load -> CPU")
        self.load_into_cpu_button.setToolTip(
            "After a successful compile, load the .ram image into the CPU and reset."
        )
        self.load_into_cpu_button.setEnabled(False)

        # setFont() alone doesn't render bold here: app.py applies the
        # app-wide QSS from styles.py, which sets font-family/font-size on
        # QPushButton -- once a stylesheet touches any font property, Qt
        # stops merging in the widget's QFont for the rest (font-weight
        # silently resets to normal). An explicit "font-weight: bold;"
        # rule wins instead.
        self.compile_button.setStyleSheet("font-weight: bold;")
        self.load_into_cpu_button.setStyleSheet("font-weight: bold;")

        toolbar.addStretch(1)
        toolbar.addWidget(self.compile_button)
        toolbar.addWidget(self.load_into_cpu_button)

        # Editor / Messages splitter
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter, 1)

        mono = self.font()
        mono.setFamily("Courier New")
        mono.setPointSize(12)

        ed_box = QWidget()
        ed_lay = QVBoxLayout(ed_box)
        ed_lay.setContentsMargins(0, 0, 0, 0)
        ed_lay.addWidget(QLabel("Source  (.asm)"))
        self.editor = QTextEdit()
        self.editor.setFont(mono)
        self.editor.setTabStopDistance(
            4 * self.editor.fontMetrics().horizontalAdvance(" ")
        )
        # Assembly source relies on column alignment (label / mnemonic /
        # operand / comment). QTextEdit word-wraps by default, which folds
        # long aligned lines onto the next row and makes the formatting
        # look "stripped" as soon as a line is wider than the pane. Disable
        # wrapping so long lines scroll horizontally instead, preserving
        # the on-disk formatting exactly as loaded.
        self.editor.setLineWrapMode(QTextEdit.NoWrap)
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

        self.compile_button.clicked.connect(self.on_compile)
        self.load_into_cpu_button.clicked.connect(self.on_load_into_cpu)

    # -------------------------------------------------------- file I/O ------

    def on_open(self):
        dlg = QFileDialog(self, "Open Assembly Source")
        dlg.setOption(QFileDialog.DontUseNativeDialog)
        dlg.setAcceptMode(QFileDialog.AcceptOpen)
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setNameFilters([
            "Assembly Files (*.asm)",
            "Listing Files (*.lst)",
            "RAM Image (*.ram)",
            "ROM Files (*.rom)",
            "All Files (*)",
        ])
        dlg.selectNameFilter("Assembly Files (*.asm)")
        dlg.setDefaultSuffix("asm")
        if self.current_path:
            dlg.setDirectory(str(self.current_path.parent))
        else:
            dlg.setDirectory(_default_open_dir())
        if dlg.exec_() != QFileDialog.Accepted:
            return
        path = Path(dlg.selectedFiles()[0])
        try:
            self.editor.setPlainText(
                path.read_text(encoding="utf-8", errors="replace")
            )
        except Exception as exc:
            QMessageBox.critical(self, "Open failed", str(exc))
            return
        self.current_path = path
        self.setWindowTitle(f"Assembler / Editor  -  {path.name}")
        self.statusBar().showMessage(f"Opened: {path}", 4000)

    def on_save(self):
        if self.current_path is None:
            self.on_save_as()
        elif not os.access(str(self.current_path.parent), os.W_OK):
            # Source is in a read-only location (e.g. /usr/share on Pi) — save elsewhere
            self.on_save_as()
        else:
            self._write_source(self.current_path)

    def on_save_as(self):
        dlg = QFileDialog(self, "Save Assembly Source")
        dlg.setOption(QFileDialog.DontUseNativeDialog)
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        dlg.setNameFilters(["Assembly Files (*.asm)", "All Files (*)"])
        dlg.selectNameFilter("Assembly Files (*.asm)")
        dlg.setDefaultSuffix("asm")
        if self.current_path and os.access(str(self.current_path.parent), os.W_OK):
            dlg.setDirectory(str(self.current_path.parent))
        else:
            dlg.setDirectory(_default_save_dir())
        if self.current_path:
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
        self.setWindowTitle(f"Assembler / Editor  -  {path.name}")

    def _write_source(self, path: Path):
        try:
            path.write_text(self.editor.toPlainText(), encoding="utf-8")
            self.statusBar().showMessage(f"Saved: {path}", 4000)
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", str(exc))

    # ----------------------------------------------------------- compile ----

    def on_compile(self):
        self.messages.clear()
        self._last_bytecode = None
        self.load_into_cpu_button.setEnabled(False)

        result = self._runner.compile(self.editor.toPlainText())
        if result is None:
            self.messages.append("Cannot compile: compiler_core / das.py not available.")
            return

        for msg in result.messages:
            self.messages.append(msg)

        if result.success and result.bytecode:
            self._last_bytecode = bytes(result.bytecode)
            self._save_ram_image(self._last_bytecode)
            self.load_into_cpu_button.setEnabled(self._host is not None)
        else:
            self.statusBar().showMessage("Compilation failed", 4000)

    def _save_ram_image(self, bytecode: bytes):
        """Determine output path then delegate image writing to the runner."""
        # Auto-save alongside the source only if that directory is writable.
        # On Pi, Data/ is in /usr/share (root-owned) so we must redirect.
        if self.current_path is not None and os.access(str(self.current_path.parent), os.W_OK):
            out_path = self.current_path.with_suffix(".ram")
        else:
            dlg = QFileDialog(self, "Save RAM Image")
            dlg.setOption(QFileDialog.DontUseNativeDialog)
            dlg.setAcceptMode(QFileDialog.AcceptSave)
            dlg.setNameFilters(["RAM Image (*.ram)", "All Files (*)"])
            dlg.selectNameFilter("RAM Image (*.ram)")
            dlg.setDefaultSuffix("ram")
            dlg.setDirectory(_default_save_dir())
            # Pre-fill filename from current source if available
            if self.current_path:
                dlg.selectFile(self.current_path.with_suffix(".ram").name)
            else:
                dlg.selectFile("untitled.ram")
            if dlg.exec_() != QFileDialog.Accepted:
                self.messages.append("RAM image not saved (cancelled).")
                return
            out_path = Path(dlg.selectedFiles()[0])
            if out_path.suffix.lower() != ".ram":
                out_path = out_path.with_suffix(".ram")

        try:
            self._runner.write_ram(bytecode, out_path)
            self.messages.append(f"RAM image written to: {out_path}")
            self.statusBar().showMessage(f"Compiled  ->  {out_path.name}", 4000)
        except Exception as exc:
            self.messages.append(f"Failed to write RAM image: {exc}")
            self.statusBar().showMessage("Write failed", 4000)
            return

        self._save_listing(out_path.with_suffix(".lst"))

    def _save_listing(self, lst_path: Path):
        """Generate and write the .lst listing alongside the .ram image."""
        source_label = str(self.current_path) if self.current_path else None
        listing = self._runner.generate_listing(self.editor.toPlainText(), source_path=source_label)
        if listing is None:
            return  # back-end unavailable; RAM image already reported that above
        if not listing.success:
            self.messages.append("Listing not written:")
            for msg in listing.messages:
                self.messages.append(f"  {msg}")
            return
        try:
            lst_path.write_text(listing.text, encoding="utf-8")
            self.messages.append(f"Listing written to: {lst_path}")
        except Exception as exc:
            self.messages.append(f"Failed to write listing: {exc}")

    # -------------------------------------------------- load into CPU -------

    def on_load_into_cpu(self):
        if self._last_bytecode is None or self._host is None:
            return
        # Must be ON to load a file — same gate as BebopMain._open_project()
        # (File -> Open ROM/RAM). With the calculator off there's no powered
        # board to load a program onto, and doing so anyway would silently
        # write into RAM that power-on is about to overwrite/reset regardless.
        calc = getattr(self._host, "_calc_win", None)
        if calc is None or not calc.powered:
            QMessageBox.warning(
                self, "Calculator Off",
                "The calculator must be switched ON before you can load a "
                "program into it.\n\n"
                "Press the On\\Off button on the calculator, then try again."
            )
            return
        n = self._runner.load_into_cpu(self._last_bytecode, self._host.cpu)
        # Normally a load-and-reset blanks the calculator display (same as
        # an explicit Reset). But with the Workbench open and the calc on,
        # the user is watching a live board -- loading a program shouldn't
        # visibly disturb the calc screen, so skip the clear in that case.
        skip_calc_clear = self._host._workbench_open_and_calc_on()
        self._host._do_reset(clear_calc_display=not skip_calc_clear)
        addr = self._runner.LOAD_ADDR
        self._host.msg_display.message(
            f"Loaded compiled image ({n} bytes) into CPU @ ${addr:04X}."
        )
        self.messages.append(
            f"-> Image ({n} bytes) loaded into Beboputer CPU @ ${addr:04X} and reset."
        )

    # --------------------------------------------------------- menu bar -----

    def _mk(self, text, slot, shortcut=None, tip=None) -> QAction:
        a = QAction(text, self)
        a.triggered.connect(slot)
        if shortcut is not None:
            a.setShortcut(shortcut)
        if tip:
            a.setStatusTip(tip)
        return a

    def _build_menu(self):
        mb = self.menuBar()
        mb.setStyleSheet("QMenuBar { font-size: 15pt; } QMenu { font-size: 15pt; }")

        fm = mb.addMenu("&File")
        fm.addAction(self._mk("&New",              self.on_new,     QKeySequence.New))
        fm.addAction(self._mk("&Open...",          self.on_open,    QKeySequence.Open))
        fm.addAction(self._mk("&Save",             self.on_save,    QKeySequence.Save))
        fm.addAction(self._mk("Save &As...",       self.on_save_as, QKeySequence.SaveAs))
        fm.addSeparator()
        fm.addAction(self._mk("&Assemble",         self.on_compile, "F5"))
        fm.addSeparator()
        fm.addAction(self._mk("&Font...",          self.on_font))
        fm.addAction(self._mk("Printer Set&up...", self.on_page_setup))
        fm.addAction(self._mk("&Print...",         self.on_print,   QKeySequence.Print))
        fm.addSeparator()
        fm.addAction(self._mk("E&xit",             self.close,      "Ctrl+Q"))

        em = mb.addMenu("&Edit")
        em.addAction(self._mk("Cu&t",          self.editor.cut,   QKeySequence.Cut))
        em.addAction(self._mk("&Copy",         self.editor.copy,  QKeySequence.Copy))
        em.addAction(self._mk("&Paste",        self.editor.paste, QKeySequence.Paste))
        em.addSeparator()
        em.addAction(self._mk("&Find...",      self.on_find,      QKeySequence.Find))
        em.addAction(self._mk("Find &Next",    self.on_find_next, QKeySequence.FindNext))
        em.addAction(self._mk("&Go to Line...",self.on_goto_line, "Ctrl+G"))

        im = mb.addMenu("&Insert")
        dm = im.addMenu("&Directive")
        for label, snippet in (
            (".ORG <integer>",            "        .ORG    $4000               # start address\n"),
            ("<Label>: .BYTE <integer>",  "LABEL:  .BYTE   $00                 # reserve 1 byte\n"),
            ("<Label>: .2BYTE <integer>", "LABEL:  .2BYTE  $0000               # reserve 2 bytes\n"),
            (".4BYTE <integer>",          "        .4BYTE  $00000000           # reserve 4 bytes\n"),
            ("<Label>: .EQU <integer>",   "LABEL:  .EQU    $00                 # constant\n"),
            (".END <integer>",            "        .END    $4000               # end of program\n"),
        ):
            dm.addAction(self._mk(label, lambda _=False, s=snippet: self._insert_text(s)))

        instr = im.addMenu("I&nstruction")
        for label, snippet in (
            ("Implied",             "        NOP                         # implied\n"),
            ("Immediate",          "        LDA     $00                 # immediate\n"),
            ("Big Immediate",      "        BLDX    $0000               # 16-bit immediate\n"),
            ("Absolute",           "        LDA     [$4000]             # direct\n"),
            ("Indexed",            "        LDA     [$4000,X]           # indexed\n"),
            ("Indirect",           "        JMP     [[$4000]]           # indirect\n"),
            ("PreIndexed",         "        LDA     [[$4000,X]]         # pre-indexed indirect\n"),
        ):
            instr.addAction(self._mk(label, lambda _=False, s=snippet: self._insert_text(s)))

        im.addSeparator()
        im.addAction(self._mk("Insert &String...", self.on_insert_string))
        im.addAction(self._mk("Insert &File...",   self.on_insert_file))

    # ------------------------------------------------------- file menu ------

    def on_new(self):
        if self.editor.toPlainText().strip():
            ans = QMessageBox.question(
                self, "New File",
                "Discard the current source and start a new file?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            if ans != QMessageBox.Yes:
                return
        self.editor.clear()
        self.messages.clear()
        self.current_path = None
        self._last_bytecode = None
        self.load_into_cpu_button.setEnabled(False)
        self.setWindowTitle("Assembler / Editor")
        self.statusBar().showMessage("New file", 3000)

    def on_font(self):
        font, ok = QFontDialog.getFont(self.editor.font(), self, "Editor Font")
        if not ok:
            return
        self.editor.setFont(font)
        self.editor.setTabStopDistance(
            4 * self.editor.fontMetrics().horizontalAdvance(" ")
        )
        self.messages.setFont(font)

    def _ensure_printer(self) -> QPrinter:
        if self._printer is None:
            self._printer = QPrinter(QPrinter.HighResolution)
        return self._printer

    def on_page_setup(self):
        dlg = QPageSetupDialog(self._ensure_printer(), self)
        dlg.exec_()

    def on_print(self):
        printer = self._ensure_printer()
        dlg = QPrintDialog(printer, self)
        dlg.setWindowTitle("Print Source")
        if dlg.exec_() == QPrintDialog.Accepted:
            self.editor.print_(printer)

    # ------------------------------------------------------- edit menu ------

    def on_find(self):
        text, ok = QInputDialog.getText(
            self, "Find", "Find text:", text=self._find_query
        )
        if not ok:
            return
        self._find_query = text
        if text:
            self._do_find(text)

    def on_find_next(self):
        if not self._find_query:
            self.on_find()
            return
        self._do_find(self._find_query)

    def _do_find(self, text):
        if not self.editor.find(text):
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.editor.setTextCursor(cursor)
            if not self.editor.find(text):
                self.statusBar().showMessage(f"Not found: {text!r}", 3000)
            else:
                self.statusBar().showMessage(f"Wrapped to top.  Found {text!r}.", 3000)

    def on_goto_line(self):
        block_count = self.editor.document().blockCount()
        line, ok = QInputDialog.getInt(
            self, "Go to Line", f"Line number (1–{block_count}):",
            1, 1, block_count, 1,
        )
        if not ok:
            return
        block  = self.editor.document().findBlockByNumber(line - 1)
        cursor = self.editor.textCursor()
        cursor.setPosition(block.position())
        self.editor.setTextCursor(cursor)
        self.editor.ensureCursorVisible()

    # ----------------------------------------------------- insert menu ------

    def _insert_text(self, text: str):
        self.editor.textCursor().insertText(text)
        self.editor.setFocus()

    def on_insert_string(self):
        text, ok = QInputDialog.getText(
            self, "Insert String",
            "String to embed as .BYTE data (null-terminated):",
        )
        if not ok or not text:
            return
        blist  = [f"${ord(c):02X}" for c in text] + ["$00"]
        chunks = [blist[i:i+8] for i in range(0, len(blist), 8)]
        snippet = (
            f"        # \"{text}\"\n"
            + "\n".join(f"        .BYTE   {', '.join(c)}" for c in chunks)
            + "\n"
        )
        self._insert_text(snippet)

    def on_insert_file(self):
        dlg = QFileDialog(self, "Insert File at Cursor")
        dlg.setOption(QFileDialog.DontUseNativeDialog)
        dlg.setAcceptMode(QFileDialog.AcceptOpen)
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setNameFilters(["Assembly / Text (*.asm *.txt)", "All Files (*)"])
        if self.current_path:
            dlg.setDirectory(str(self.current_path.parent))
        else:
            dlg.setDirectory(_default_open_dir())
        if dlg.exec_() != QFileDialog.Accepted:
            return
        path = Path(dlg.selectedFiles()[0])
        try:
            self._insert_text(path.read_text(encoding="utf-8", errors="replace"))
            self.statusBar().showMessage(f"Inserted: {path}", 4000)
        except Exception as exc:
            QMessageBox.critical(self, "Insert failed", str(exc))

    # ---------------------------------------------------- window menu -------

    def on_toggle_messages(self, checked: bool):
        parent = self.messages.parentWidget()
        if parent is not None:
            parent.setVisible(checked)

    # ------------------------------------------------------ help menu -------

    def on_about(self):
        QMessageBox.about(
            self, "About Assembler / Editor",
            "<b>Beboputer Assembler / Editor</b><br><br>"
            "Edit .asm source, assemble via the DAS engine, and "
            "load the resulting RAM image straight into the Beboputer CPU."
        )
