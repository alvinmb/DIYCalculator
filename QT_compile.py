
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QLabel,
    QSplitter,
)

from compiler_core import Compiler


class CompilerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("DIY Calculator Compiler")
        self.resize(900, 600)

        self.compiler = Compiler()
        self.current_path: Path | None = None

        central = QWidget(self)
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        # Toolbar row
        toolbar_layout = QHBoxLayout()
        main_layout.addLayout(toolbar_layout)

        self.open_button = QPushButton("Open")
        self.save_button = QPushButton("Save")
        self.save_as_button = QPushButton("Save As")
        self.compile_button = QPushButton("Compile")

        toolbar_layout.addWidget(self.open_button)
        toolbar_layout.addWidget(self.save_button)
        toolbar_layout.addWidget(self.save_as_button)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.compile_button)

        # Splitter: editor (top) / messages (bottom)
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter, 1)

        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        self.editor_label = QLabel("Source")
        self.editor = QTextEdit()
        self.editor.setTabStopDistance(4 * self.editor.fontMetrics().horizontalAdvance(" "))

        editor_layout.addWidget(self.editor_label)
        editor_layout.addWidget(self.editor, 1)

        messages_container = QWidget()
        messages_layout = QVBoxLayout(messages_container)
        messages_layout.setContentsMargins(0, 0, 0, 0)

        self.messages_label = QLabel("Messages")
        self.messages = QTextEdit()
        self.messages.setReadOnly(True)

        messages_layout.addWidget(self.messages_label)
        messages_layout.addWidget(self.messages, 1)

        splitter.addWidget(editor_container)
        splitter.addWidget(messages_container)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        # Wire up signals
        self.open_button.clicked.connect(self.on_open)
        self.save_button.clicked.connect(self.on_save)
        self.save_as_button.clicked.connect(self.on_save_as)
        self.compile_button.clicked.connect(self.on_compile)

    # --- File handling ---

    def on_open(self):
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Open Source File",
            "",
            "Source Files (*.txt *.src *.diy);;All Files (*)",
        )
        if not path_str:
            return

        path = Path(path_str)
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{exc}")
            return

        self.current_path = path
        self.editor.setPlainText(text)
        self.statusBar().showMessage(f"Opened: {path}", 5000)

    def on_save(self):
        if self.current_path is None:
            self.on_save_as()
            return

        try:
            self.current_path.write_text(self.editor.toPlainText(), encoding="utf-8")
            self.statusBar().showMessage(f"Saved: {self.current_path}", 5000)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{exc}")

    def on_save_as(self):
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Save Source File As",
            "",
            "Source Files (*.txt *.src *.diy);;All Files (*)",
        )
        if not path_str:
            return

        path = Path(path_str)
        try:
            path.write_text(self.editor.toPlainText(), encoding="utf-8")
            self.current_path = path
            self.statusBar().showMessage(f"Saved: {path}", 5000)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{exc}")

    # --- Compilation ---

    def on_compile(self):
        source = self.editor.toPlainText()
        self.messages.clear()

        result = self.compiler.compile_source(source)

        for msg in result.messages:
            self.messages.append(msg)

        if result.success and result.bytecode is not None:
            # Optionally auto-save bytecode next to source
            if self.current_path is not None:
                out_path = self.current_path.with_suffix(".bin")
                try:
                    out_path.write_bytes(result.bytecode)
                    self.messages.append(f"Bytecode written to: {out_path}")
                except Exception as exc:
                    self.messages.append(f"Failed to write bytecode: {exc}")
        else:
            # Highlight failure in status bar
            self.statusBar().showMessage("Compilation failed", 5000)


def main():
    app = QApplication(sys.argv)
    win = CompilerWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()