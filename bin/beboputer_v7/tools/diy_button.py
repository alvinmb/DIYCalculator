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

"""DIY Calculator Button -- right-click (when calculator is off) to configure.

Each button writes a single byte to the fixed memory-mapped port $F011
when clicked.  Port is not user-configurable.

Right-click opens Configure Button Attributes (only when the calc is off).
Load Button File and Restore Defaults are on the calculator File menu.

File format  (defbuttons.ini / *.ini)  --  DIY Calculator Buttons
------------------------------------------------------------------
#FILE TYPE:DIY Calculator Buttons (*.ini) File
#GENERATOR:Beboputer v7
#DATE-TIME:Jan 01 00:00:00 2025
#SOURCEWAS:N/A

#COLOR CODES USED
#COLOR 0 = BLACK
#COLOR 1 = RED
#COLOR 2 = GREEN
#COLOR 3 = YELLOW
#COLOR 4 = BLUE
#COLOR 5 = MAGENTA
#COLOR 6 = CYAN


[Button 1]
Code= $41
Annotation=A
Color= 0
Description=Hexadecimal digit

Color is stored as the palette index (0-6).
Code is the hex byte written to port $F011 on click.
"""

import configparser
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QPushButton, QDialog, QFormLayout, QLineEdit,
    QComboBox, QVBoxLayout, QHBoxLayout,
)

# Port is fixed -- not editable by the user.
_FIXED_PORT = 0xF011

# Writable user-data directory -- %APPDATA%\PY-DIYCALCULATOR\
# Using APPDATA ensures writes succeed whether installed to Program Files or not.
import os as _os
_USER_DATA_DIR = Path(_os.environ.get("APPDATA", Path.home())) / "PY-DIYCALCULATOR"
_CONFIG_DIR    = _USER_DATA_DIR / "Config"
_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
_DEFBUTTONS_PATH = _CONFIG_DIR / "defbuttons.ini"

# Buttons directory (user-writable)
_BUTTONS_DIR = _USER_DATA_DIR / "buttons"
_BUTTONS_DIR.mkdir(parents=True, exist_ok=True)

# -- Colour palette -----------------------------------------------------------
# Each entry: (display_name, hex_color)
COLORS = [
    ("Black",   "#000000"),
    ("Red",     "#cc0000"),
    ("Green",   "#00aa00"),
    ("Yellow",  "#aaaa00"),
    ("Blue",    "#0000cc"),
    ("Magenta", "#cc00cc"),
    ("Cyan",    "#00cccc"),
]


def _color_hex(index: int) -> str:
    if 0 <= index < len(COLORS):
        return COLORS[index][1]
    return COLORS[0][1]


def _color_index(value: str) -> int:
    """Map a color hex string or color *name* to its palette index.

    ``load_defbuttons_file()`` falls back to this when the ``Color=``
    value isn't a plain digit (e.g. not "5"). Without a name match, a
    hand-edited file using a name from the file's own documented
    convention -- "#COLOR 5 = MAGENTA" -- (e.g. ``Color= Magenta``)
    would silently fall through to Black instead of the intended color,
    since only hex strings like "#cc00cc" used to be recognised here.
    """
    v = value.strip()
    for i, (name, h) in enumerate(COLORS):
        if v.lower() == h.lower() or v.lower() == name.lower():
            return i
    return 0


def _parse_code(raw: str) -> int:
    """Parse Code value: '$XX' or plain hex digits or decimal."""
    raw = raw.strip()
    if raw.startswith('$'):
        try:
            return int(raw[1:], 16) & 0xFF
        except ValueError:
            pass
    try:
        return int(raw, 16) & 0xFF
    except ValueError:
        pass
    try:
        return int(raw) & 0xFF
    except ValueError:
        return 0


# -- defbuttons.ini helpers ---------------------------------------------------

_FILE_HEADER = (
    "#FILE TYPE:DIY Calculator Buttons (*.ini) File\n"
    "#GENERATOR:Beboputer v7\n"
    "#DATE-TIME:{dt}\n"
    "#SOURCEWAS:N/A\n"
    "\n"
    "#COLOR CODES USED\n"
    "#COLOR 0 = BLACK\n"
    "#COLOR 1 = RED\n"
    "#COLOR 2 = GREEN\n"
    "#COLOR 3 = YELLOW\n"
    "#COLOR 4 = BLUE\n"
    "#COLOR 5 = MAGENTA\n"
    "#COLOR 6 = CYAN\n"
    "\n"
)


def load_defbuttons_file(path=None) -> dict:
    """Load all [Button N] sections from defbuttons.ini (or *path*).

    Returns {index: ButtonDef}.  Returns an empty dict if the file does
    not exist or contains no valid button sections.
    """
    p = Path(path) if path else _DEFBUTTONS_PATH
    if not p.exists():
        return {}

    cfg = configparser.ConfigParser(
        comment_prefixes=('#', ';', "'"),
        inline_comment_prefixes=None,
        strict=False,
    )
    cfg.read(str(p), encoding="utf-8")

    result = {}
    for section in cfg.sections():
        parts = section.split()
        if len(parts) == 2 and parts[0].lower() == 'button':
            try:
                idx = int(parts[1])
                if idx <= 0:
                    continue
                sec = cfg[section]
                d = ButtonDef()
                d.label = sec.get('annotation', '').strip().strip('"')
                d.value = _parse_code(sec.get('code', '00'))
                raw_color = sec.get('color', '0').strip()
                try:
                    d.color_index = int(raw_color)
                except ValueError:
                    d.color_index = _color_index(raw_color)
                d.description = sec.get('description', 'Unassigned').strip().strip('"')
                result[idx] = d
            except ValueError:
                pass

    return result


def save_defbuttons_file(buttons: dict, path=None):
    """Write all buttons to defbuttons.ini (or *path*).

    Parameters
    ----------
    buttons : dict
        {index: ButtonDef} mapping -- all buttons to persist.
    path : str or Path, optional
        Override destination; defaults to _DEFBUTTONS_PATH.
    """
    p = Path(path) if path else _DEFBUTTONS_PATH
    dt = datetime.now().strftime("%b %d %H:%M:%S %Y")
    with open(str(p), "w", encoding="utf-8") as fh:
        fh.write(_FILE_HEADER.format(dt=dt))
        for idx in sorted(buttons):
            d = buttons[idx]
            fh.write(f"\n[Button {idx}]\n")
            fh.write(f"Code= ${d.value:02X}\n")
            fh.write(f"Annotation={d.label}\n")
            fh.write(f"Color= {d.color_index}\n")
            fh.write(f"Description={d.description}\n")


# -- ButtonDef ----------------------------------------------------------------

class ButtonDef:
    """Visual + action properties for one DIY button."""

    def __init__(self):
        self.label       = ""
        self.color_index = 0
        self.bg_color    = "#d4d0c8"    # fixed; not user-editable
        self.bold        = False
        self.port        = _FIXED_PORT
        self.value       = 0
        self.description = "Unassigned"

    @property
    def color(self) -> str:
        return _color_hex(self.color_index)

    def save(self, path: str, button_num: int = 1):
        """Write this button to a standalone .ini file."""
        save_defbuttons_file({button_num: self}, path)

    @classmethod
    def load(cls, path: str):
        """Load the first [Button N] from a .ini file."""
        result = load_defbuttons_file(path)
        if result:
            return next(iter(result.values()))
        return cls()


# -- ConfigureButtonAttributes ------------------------------------------------

class ConfigureButtonAttributes(QDialog):
    """Right-click dialog (only when calculator is off): configure a button.

    Fields: Code, Annotation, Color, Description.
    Apply writes the changes back to the button and to defbuttons.ini.
    """

    def __init__(self, defn: ButtonDef, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Button Attributes")
        self.setFixedWidth(320)
        self._defn = defn
        self._build()

    def _build(self):
        F = QFont("Arial", 12, QFont.Bold)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.setSpacing(8)

        def _lbl(text):
            from PyQt5.QtWidgets import QLabel
            l = QLabel(text)
            l.setFont(F)
            return l

        FIELD_SS = "font-size: 11pt; font-family: Arial;"

        # Code
        self.code_edit = QLineEdit(f"${self._defn.value:02X}")
        self.code_edit.setFixedWidth(80)
        self.code_edit.setStyleSheet(FIELD_SS)
        code_row = QHBoxLayout()
        code_row.addWidget(self.code_edit)
        code_row.addStretch()
        form.addRow(_lbl("Code:"), code_row)

        # Annotation
        self.annot_edit = QLineEdit(self._defn.label)
        self.annot_edit.setStyleSheet(FIELD_SS)
        form.addRow(_lbl("Annotation:"), self.annot_edit)

        # Color
        self.color_combo = QComboBox()
        self.color_combo.setStyleSheet("font-size: 11pt; font-family: Arial;")
        for name, _ in COLORS:
            self.color_combo.addItem(name)
        self.color_combo.setCurrentIndex(self._defn.color_index)
        form.addRow(_lbl("Color:"), self.color_combo)

        # Description
        self.desc_edit = QLineEdit(self._defn.description)
        self.desc_edit.setStyleSheet(FIELD_SS)
        form.addRow(_lbl("Description"), self.desc_edit)

        layout.addLayout(form)

        # Apply button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        apply_btn = QPushButton("Apply")
        apply_btn.setFont(F)
        apply_btn.setStyleSheet("font-size: 11pt; font-weight: normal; font-family: Arial; color: black;")
        apply_btn.setDefault(True)
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.accept)
        btn_row.addWidget(apply_btn)
        layout.addLayout(btn_row)

    def get_defn(self) -> ButtonDef:
        """Return a new ButtonDef populated from the current field values."""
        d = ButtonDef()
        d.label       = self.annot_edit.text().strip()
        d.color_index = self.color_combo.currentIndex()
        d.bold        = self._defn.bold
        d.bg_color    = self._defn.bg_color
        d.value       = _parse_code(self.code_edit.text())
        d.description = self.desc_edit.text().strip() or "Unassigned"
        return d


# -- DIYButton ----------------------------------------------------------------

_BTN_CSS = """
    QPushButton {{
        color:            {color};
        background-color: {bg};
        border:           1px solid #888;
        border-top-color: #fff;
        border-left-color:#fff;
        border-radius:    2px;
        padding:          2px 4px;
    }}
    QPushButton:pressed {{
        border-top-color:   #888;
        border-left-color:  #888;
        border-bottom-color:#fff;
        border-right-color: #fff;
        background-color:   #c0bdb5;
    }}
    QToolTip {{
        background-color: #ffffcc;
        color: #000000;
        border: 1px solid #808080;
        padding: 2px 4px;
    }}
"""


class DIYButton(QPushButton):
    """A calculator button with an editable ButtonDef.

    Left-click  -- writes defn.value to port $F011 via the CPU.
    Right-click -- opens Configure Button Attributes (only when calc is off).
                   Load Button File and Restore Defaults are on File menu.

    Parameters
    ----------
    powered_fn : callable() -> bool, optional
        Returns True when the calculator is on; right-click is ignored then.
    button_index : int
        1-based index used when persisting to defbuttons.ini.
    save_fn : callable(index, ButtonDef), optional
        Called after Apply to persist the single-button change.
    """

    def __init__(self, label="", color="#000000", bg="#d4d0c8",
                 min_w=46, min_h=36, bold=False, cpu=None,
                 powered_fn=None, button_index=0, save_fn=None,
                 parent=None):
        super().__init__(parent)
        self._cpu          = cpu
        self._powered_fn   = powered_fn
        self._button_index = button_index
        self._save_fn      = save_fn

        self._defn             = ButtonDef()
        self._defn.label       = label
        self._defn.color_index = _color_index(color)
        self._defn.bg_color    = bg
        self._defn.bold        = bold

        self._min_w = min_w
        self._min_h = min_h
        self._apply_defn()

    # -- appearance -----------------------------------------------------------

    def _apply_defn(self):
        d = self._defn
        self.setText(d.label)
        font = QFont("Arial", 10, QFont.Bold if d.bold else QFont.Normal)
        self.setFont(font)
        self.setStyleSheet(_BTN_CSS.format(color=d.color, bg=d.bg_color))
        self.setMinimumSize(QSize(self._min_w, self._min_h))
        self.setMaximumSize(QSize(self._min_w * 4, self._min_h))

    def apply_button_def(self, defn: ButtonDef):
        """Apply an externally-loaded ButtonDef (e.g. from defbuttons.ini).

        The button's background colour and bold flag are preserved.
        """
        defn.bg_color = self._defn.bg_color
        defn.bold     = self._defn.bold
        self._defn    = defn
        self._apply_defn()

    # -- mouse events ---------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._open_editor()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            super().mouseReleaseEvent(event)
            self._execute()
        else:
            super().mouseReleaseEvent(event)

    # -- action ---------------------------------------------------------------

    def _execute(self):
        if self._cpu is None:
            return
        # Send the button's Code= value exactly as stored in defbuttons.ini,
        # with no translation. This used to reinterpret codes $30-$39/$41-$46
        # as ASCII hex digits and rewrite them down to raw nibbles 0-15 --
        # but every digit/hex-letter button in the current defbuttons.ini
        # already stores its raw nibble code directly (e.g. "4" = $04, not
        # $34), so that translation had no legitimate target left. Its only
        # live effect was silently corrupting any *non-digit* button whose
        # Code happened to land in those same ASCII ranges by coincidence --
        # e.g. Cos ($39) was rewritten to $09, Tan ($38) to $08, Log ($37) to
        # $07, and n! ($36) to $06, so keypad-reading programs never saw the
        # byte the button was actually configured to send.
        self._cpu._write(_FIXED_PORT, self._defn.value)

    # -- editor ---------------------------------------------------------------

    def _open_editor(self):
        """Open Configure Button Attributes (only when the calculator is off)."""
        if self._powered_fn is not None and self._powered_fn():
            return
        dlg = ConfigureButtonAttributes(self._defn, self)
        if dlg.exec_() == QDialog.Accepted:
            self._defn = dlg.get_defn()
            self._apply_defn()
            if self._save_fn is not None:
                self._save_fn(self._button_index, self._defn)
