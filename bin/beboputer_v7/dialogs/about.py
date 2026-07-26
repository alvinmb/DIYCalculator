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

"""About dialog."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout

from .. import __version__
from ..styles import C


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About PY-DIYCALCULATOR")
        self.setFixedSize(460, 300)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("PY-DIYCALCULATOR")
        title.setStyleSheet(f"color:{C['blue']}; font-size:19px; font-weight:bold; letter-spacing:3px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sub = QLabel(f"Python/PyQt5 Edition  —  v{__version__}")
        sub.setStyleSheet(f"color:{C['green_mid']}; font-size:14px;")
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)

        info = QLabel(
            "Based on the Beboputer virtual 8-bit CPU from\n"
            '"How Computers Do Math"\nby Clive "Max" Maxfield & Alvin Brown\n\n'
            "Rewritten\nin Python 3 + PyQt5."
        )
        info.setStyleSheet(f"color:{C['green_mid']}; font-size:17px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        ok = QPushButton("Dismiss")
        ok.clicked.connect(self.accept)
        layout.addWidget(ok, alignment=Qt.AlignCenter)
