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

"""ButtonDef + defbuttons.ini helpers -- pure logic, no Qt dependency.

Split out of diy_button.py (2026-08-02): that module did an unconditional
top-level ``from PyQt5.QtCore import ...`` for its two UI classes
(ConfigureButtonAttributes, DIYButton), which meant *any* import from it --
including beboputer_tk.panels.diy_button's import of the plain-data pieces
below -- pulled the entire PyQt5 package into PyInstaller's dependency graph
for the tkinter build. That's why the "tkinter" Windows installer kept
bundling PyQt5/Qt5 DLLs: beboputer_tk never imports PyQt5 itself, but this
one transitive import made PyInstaller's static analysis think it needed to.

Everything here is plain Python (configparser, pathlib, dataclasses-style
attributes) -- safe for both the PyQt5 build and the tkinter build to import
without dragging in the other UI toolkit. diy_button.py re-exports all of
these names unchanged, so beboputer_v7 code that already does
``from .diy_button import ButtonDef, ...`` keeps working without edits.

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
import os as _os
from datetime import datetime
from pathlib import Path

# Port is fixed -- not editable by the user.
_FIXED_PORT = 0xF011

# Writable user-data directory -- %APPDATA%\PY-DIYCALCULATOR\
# Using APPDATA ensures writes succeed whether installed to Program Files or not.
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
