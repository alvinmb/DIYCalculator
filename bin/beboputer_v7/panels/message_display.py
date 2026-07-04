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

"""Message Display — always-on diagnostic log panel.

Shows system messages from the emulator itself: step results, resets,
halts, file-load confirmations, breakpoint hits, clock changes, etc.

Completely independent of the calculator power state — always active.
"""

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QLabel


_CSS_HEADER = """
    QLabel {
        background:   #2e2e2e;
        color:        #aaaaaa;
        font-family:  Arial;
        font-size:    11px;
        padding:      2px 6px;
        border-bottom: 1px solid #555;
    }
"""

_CSS_LOG = """
    QTextEdit {
        background:  #1c1c1c;
        color:       #c8c8c8;
        border:      none;
        font-family: 'Courier New';
        font-size:   16px;
    }
"""


class MessageDisplay(QWidget):
    """Always-on diagnostic log — shows emulator system messages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    # ── construction ──────────────────────────────────────────────────────────

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        hdr = QLabel("▸ Message Display")
        hdr.setStyleSheet(_CSS_HEADER)
        layout.addWidget(hdr)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Courier New", 13))
        self.log.setStyleSheet(_CSS_LOG)
        layout.addWidget(self.log)

    # ── public API ────────────────────────────────────────────────────────────

    def message(self, text: str):
        """Append a line to the log. Always visible regardless of power state."""
        self.log.append(text)
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())
