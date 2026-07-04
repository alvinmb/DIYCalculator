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

"""On-screen Keyboard — sends ASCII bytes to port $F011.

Layout matches the original DIY Calculator Keyboard screenshot:

  Row 0 :  ESC  !  @  #  $  %  ^  Amp  *  (  )  _  +  [HEX]  "
  Row 1 :  ~  1  2  3  4  5  6  7  8  9  0  -  =  BSpace  <
  Row 2 :  TAB  Q  W  E  R  T  Y  U  I  O  P  [  ]  \\  >
  Row 3 :  CAPS  A  S  D  F  G  H  J  K  L  :  '  ENTER  ?
  Row 4 :  SHIFT  Z  X  C  V  B  N  M  .  .  /  Le  Ri  ;
  Row 5 :  CTRL  ALT  [   SPACE   ]  Up  Do  |

The HEX display (top-right, row 0) shows $XX for the last key
pressed.  CAPS and SHIFT toggle letter capitalisation.  Arrow keys
(Le/Ri/Up/Do) send control codes 0x1C–0x1F.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout,
)

_PORT = 0xF011   # memory-mapped input port

_KW  = 48        # standard key width  (px)  (+25 %)
_KH  = 58        # key height          (px)  (+25 % then +20)
_SP  =  3        # gap between keys    (px)  (+25 %)

_BTN_CSS = """
    QPushButton {{
        color:            {fg};
        background-color: #d4d0c8;
        border:           1px solid #888;
        border-top-color: #fff;
        border-left-color:#fff;
        border-radius:    2px;
        padding:          1px;
        font-family:      Arial;
        font-size:        9pt;
        font-weight:      bold;
        min-height:       {kh}px;
        max-height:       {kh}px;
    }}
    QPushButton:pressed {{
        border-top-color:    #888;
        border-left-color:   #888;
        border-bottom-color: #fff;
        border-right-color:  #fff;
        background-color:    #c0bdb5;
    }}
    QPushButton:checked {{
        background-color: #cc0000;
        color:            #ffffff;
        border-top-color:    #888;
        border-left-color:   #888;
    }}
"""


class KeyboardPanel(QDialog):
    """On-screen keyboard.  Each key press writes one ASCII byte to $F011."""

    def __init__(self, cpu, terminal_cb=None, parent=None):
        super().__init__(parent)
        self.cpu          = cpu
        self._terminal_cb = terminal_cb   # optional: Terminal.write_char
        self._caps        = False
        self._shift       = False
        self.setWindowTitle("Keyboard")
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )
        self._build()

    # ── close hides rather than destroys so re-open works ─────────────────────

    def closeEvent(self, event):
        if getattr(self, '_app_closing', False):
            event.accept()
        else:
            event.ignore()
            self.hide()

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(_SP)
        root.setContentsMargins(6, 6, 6, 6)

        # Hex display — slotted into row 0 via None placeholder.
        self._hex = QLabel("$--")
        self._hex.setAlignment(Qt.AlignCenter)
        self._hex.setFixedSize(int(_KW * 1.55), _KH)
        self._hex.setStyleSheet(
            "background:#000000; color:#ffffff; "
            "font-family:'Courier New'; font-weight:bold; font-size:14pt; "
            "border:2px inset #444444;"
        )

        for row in self._rows():
            hbox = QHBoxLayout()
            hbox.setSpacing(_SP)
            hbox.setContentsMargins(0, 0, 0, 0)
            for item in row:
                if item is None:
                    hbox.addWidget(self._hex)
                elif item[0] == "__sp__":
                    hbox.addSpacing(item[1])   # fixed-pixel spacer for column alignment
                else:
                    hbox.addWidget(self._make_btn(*item))
            hbox.addStretch()
            root.addLayout(hbox)

    # ── key factory ───────────────────────────────────────────────────────────

    def _make_btn(self, label, val, mult=1.0, fg="#000000"):
        btn = QPushButton(label)
        btn.setFixedSize(int(_KW * mult), _KH)
        btn.setFont(QFont("Arial", 9, QFont.Bold))
        btn.setStyleSheet(_BTN_CSS.format(fg=fg, kh=_KH))

        if label in ("CAPS", "SHIFT"):
            btn.setCheckable(True)
            btn.toggled.connect(
                lambda on, lbl=label: self._mod(lbl, on)
            )
        elif val is not None:
            btn.clicked.connect(
                lambda _, v=val, lbl=label: self._press(v, lbl)
            )
        # CTRL / ALT — cosmetic only

        return btn

    # ── actions ───────────────────────────────────────────────────────────────

    def _mod(self, label, on):
        if label == "CAPS":
            self._caps = on
        else:
            self._shift = on

    def _press(self, val, label):
        # Single alphabetic label → apply case modifier.
        if len(label) == 1 and label.isalpha():
            val = ord(
                label.upper() if (self._caps or self._shift) else label.lower()
            )
        val &= 0xFF
        self.cpu._write(_PORT, val)
        self._hex.setText(f"${val:02X}")
        if self._terminal_cb is not None:
            self._terminal_cb(val)

    # ── key map ───────────────────────────────────────────────────────────────

    @staticmethod
    def _rows():
        """Return list-of-rows.

        Each row item is either None (hex display slot) or a tuple:
            (label, ascii_val_or_None, width_mult, fg_colour)
        """
        def k(lbl, val, m=1.0, c="#000000"):
            return (lbl, val, m, c)

        return [
            # Row 0 — shifted / special symbols ──────────────────────────────
            [k("ESC",  27,  1.2),
             k("!",  33), k("@",  64), k("#",  35), k("$",  36),
             k("%",  37), k("^",  94), k("Amp", 38), k("*",  42),
             k("(",  40), k(")",  41), k("_",  95), k("+",  43),
             None,                                    # ← hex display
             k('"',  34)],

            # Row 1 — numbers ─────────────────────────────────────────────────
            [k("~",  126),
             k("1",  49), k("2",  50), k("3",  51), k("4",  52),
             k("5",  53), k("6",  54), k("7",  55), k("8",  56),
             k("9",  57), k("0",  48), k("-",  45), k("=",  61),
             k("BSpace", 0x04, 1.5),
             k("<",  60)],

            # Row 2 — QWERTY ──────────────────────────────────────────────────
            [k("TAB", 9, 1.4),
             k("Q", ord("Q")), k("W", ord("W")), k("E", ord("E")),
             k("R", ord("R")), k("T", ord("T")), k("Y", ord("Y")),
             k("U", ord("U")), k("I", ord("I")), k("O", ord("O")),
             k("P", ord("P")),
             k("[",  91), k("]",  93), k("\\", 92),
             k(">",  62)],

            # Row 3 — ASDF ────────────────────────────────────────────────────
            [k("CAPS", None, 1.55, "#cc0000"),
             k("A", ord("A")), k("S", ord("S")), k("D", ord("D")),
             k("F", ord("F")), k("G", ord("G")), k("H", ord("H")),
             k("J", ord("J")), k("K", ord("K")), k("L", ord("L")),
             k(":",  58), k("'",  39),
             k("ENTER", 0x05, 1.55),
             k("?",  63)],

            # Row 4 — ZXCV ────────────────────────────────────────────────────
            [k("SHIFT", None, 2.0),
             k("Z", ord("Z")), k("X", ord("X")), k("C", ord("C")),
             k("V", ord("V")), k("B", ord("B")), k("N", ord("N")),
             k("M", ord("M")),
             k(".",  46), k(".",  46), k("/",  47),
             k("Le", 0x0A), k("Ri", 0x09),
             k(";",  59)],

            # Row 5 — bottom ──────────────────────────────────────────────────
            # 191-px spacer shifts Up/Do to align under Le/Ri in row 4:
            #   row-4 left-edge of Le  = 96+480+33      = 609 px
            #   row-5 left-edge of Up  = 76+76+254+9    = 415 px
            #   spacer needed          = 609-415-3(gap) = 191 px
            [k("CTRL", None, 1.6), k("ALT", None, 1.6),
             k("SPACE", 32, 5.3),
             ("__sp__", 191, 1.0, "#000000"),
             k("Up", 0x07), k("Do", 0x08),
             k("|", 124)],
        ]
