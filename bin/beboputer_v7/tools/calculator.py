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
Classic-style scientific Calculator (merged from calc.py).

Stand-alone window launched from the Tools menu/toolbar of the main
Beboputer window.
"""

import math
from pathlib import Path

from PyQt5.QtCore import Qt, QSize, QEvent, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog,
)

from .diy_button import (
    DIYButton, ButtonDef,
    load_defbuttons_file, save_defbuttons_file,
    _DEFBUTTONS_PATH, _BUTTONS_DIR,
)
from ..paths import resource_path


# -- Default button Code + Description ----------------------------------------
# Maps button label → (hex_code, description).
# Code is the byte written to port $F011 on left-click.
# x^2 = $3D matches the reference screenshot.

_BUTTON_DEFAULTS = {
    # base-mode switches
    # NOTE: these three used to be $02/$0A/$10. $02 is the same byte a
    # digit-"2" keypress sends (DIYButton._execute() converts digits down
    # to raw nibbles 0-9, hex letters to 10-15 - see tools/diy_button.py),
    # and $0A is identical to what hex-letter "A" sends (raw nibble 10) -
    # the same kind of collision Clear Entry/digit-"1" had before CE was
    # moved to $7F. Any program that branches on these exact byte values
    # to mean "Bin"/"Dec" (see tutorial 14) would misread a plain digit
    # "2" or hex letter "A" as a mode switch. Moved to $43/$44/$45,
    # outside the 0-15 nibble range, to match the shipped
    # Config/defbuttons.ini and remove the collision for good.
    "Bin":  (0x43, "Switch to binary mode"),
    "Dec":  (0x44, "Switch to decimal mode"),
    "Hex":  (0x45, "Switch to hexadecimal mode"),
    # trig / scientific functions
    "Sin":  (0x73, "Sine of x"),
    "Cos":  (0x63, "Cosine of x"),
    "Tan":  (0x74, "Tangent of x"),
    "Log":  (0x6C, "Log base 10 of x"),
    "n!":   (0x21, "Factorial of n"),
    "x^y":  (0x5E, "x to the power y"),
    "x^3":  (0x23, "x cubed"),
    "x^2":  (0x3D, "Calculate x squared"),
    "Rx":   (0x72, "Square root of x"),
    "1/x":  (0x78, "Reciprocal of x"),
    # digits
    "0":    (0x30, "Digit 0"),
    "1":    (0x31, "Digit 1"),
    "2":    (0x32, "Digit 2"),
    "3":    (0x33, "Digit 3"),
    "4":    (0x34, "Digit 4"),
    "5":    (0x35, "Digit 5"),
    "6":    (0x36, "Digit 6"),
    "7":    (0x37, "Digit 7"),
    "8":    (0x38, "Digit 8"),
    "9":    (0x39, "Digit 9"),
    # operators
    "+":    (0x2B, "Add"),
    "--":   (0x2D, "Negate"),
    "*":    (0x2A, "Multiply"),
    "/":    (0x2F, "Divide"),
    "=":    (0x3D, "Equals / evaluate"),
    ".":    (0x2E, "Decimal point"),
    "+/-":  (0x4E, "Change sign"),
    "(":    (0x28, "Open parenthesis"),
    ")":    (0x29, "Close parenthesis"),
    # scientific extras
    "Mod":  (0x4D, "Modulo"),
    "Exp":  (0x45, "Exponent notation"),
    "Pi":   (0x50, "Pi constant"),
    "F-S": (0x46, "Float / scientific toggle"),
    # hex digits
    "A":    (0x41, "Hex digit A"),
    "B":    (0x42, "Hex digit B"),
    "C":    (0x43, "Hex digit C"),
    "D":    (0x44, "Hex digit D"),
    "E":    (0x45, "Hex digit E"),
    "F":    (0x46, "Hex digit F"),
    # control
    # NOTE: Clear/CE/Enter must stay outside $00-$0F. Digit and hex-letter
    # buttons are sent to the CPU as a raw nibble (0-15), not their ASCII
    # code (see DIYButton._execute() in diy_button.py) - so any control
    # key using a byte in that same range is indistinguishable from
    # whichever digit/hex-letter happens to convert to the same nibble.
    # CE used to be $01, which is bit-for-bit identical to what the "1"
    # digit button actually sends, so a CPU program watching for CE could
    # never reliably tell "CE" and "1" apart. $7F (ASCII DEL) is outside
    # that range and free.
    "Clear":(0x1B, "Clear display"),
    "CE":   (0x7F, "Clear entry"),
    "Back": (0x08, "Backspace"),
    "Enter":(0x0D, "Evaluate expression"),
}


# -- Stylesheet constants -----------------------------------------------------

_DISPLAY_ON_CSS = """
    QLineEdit {
        background-color: #c8f0c8;
        border: 2px inset #888;
        font-size: 18pt;
        font-weight: bold;
        font-family: "Courier New";
        padding-right: 6px;
        color: #000;
    }
"""

_DISPLAY_OFF_CSS = """
    QLineEdit {
        background-color: #6e7a6e;
        border: 2px inset #888;
        font-size: 18pt;
        font-weight: bold;
        font-family: "Courier New";
        padding-right: 6px;
        color: #4a504a;
    }
"""

_POWER_BTN_ON_CSS = """
    QPushButton {
        color: #000;
        background-color: #7ed07e;
        border: 1px solid #888;
        border-top-color: #fff;
        border-left-color: #fff;
        border-radius: 2px;
        padding: 2px 4px;
        font-weight: bold;
    }
    QPushButton:pressed {
        background-color: #6ab86a;
    }
    QToolTip {
        background-color: #ffffcc;
        color: #000000;
        border: 1px solid #808080;
        padding: 2px 4px;
    }
"""

_POWER_BTN_OFF_CSS = """
    QPushButton {
        color: #000;
        background-color: #d4d0c8;
        border: 1px solid #888;
        border-top-color: #fff;
        border-left-color: #fff;
        border-radius: 2px;
        padding: 2px 4px;
    }
    QPushButton:pressed {
        background-color: #c0bdb5;
    }
    QToolTip {
        background-color: #ffffcc;
        color: #000000;
        border: 1px solid #808080;
        padding: 2px 4px;
    }
"""

_LED_OFF_CSS = """
    QLabel {
        background:    #3a0000;
        border:        1px solid #555;
        border-radius: 10px;
        min-width:  20px;
        min-height: 20px;
        max-width:  20px;
        max-height: 20px;
    }
"""

_LED_ON_CSS = """
    QLabel {
        background:    #ff1a1a;
        border:        1px solid #cc0000;
        border-radius: 10px;
        min-width:  20px;
        min-height: 20px;
        max-width:  20px;
        max-height: 20px;
    }
"""


def _calc_make_btn(text, color="#000000", bg="#d4d0c8", min_w=46, min_h=36, bold=False, tooltip=None):
    btn = QPushButton(text)
    font = QFont("Arial", 10, QFont.Bold)
    btn.setFont(font)
    btn.setMinimumSize(QSize(min_w, min_h))
    btn.setStyleSheet(f"""
        QPushButton {{
            color: {color};
            background-color: {bg};
            border: 1px solid #888;
            border-top-color: #fff;
            border-left-color: #fff;
            border-radius: 2px;
            padding: 2px 4px;
        }}
        QPushButton:pressed {{
            border-top-color: #888;
            border-left-color: #888;
            border-bottom-color: #fff;
            border-right-color: #fff;
            background-color: #c0bdb5;
        }}
        QToolTip {{
            background-color: #ffffcc;
            color: #000000;
            border: 1px solid #808080;
            padding: 2px 4px;
        }}
    """)
    if tooltip:
        btn.setToolTip(tooltip)
    return btn


class Calculator(QMainWindow):
    """Classic-style scientific calculator with Bin/Dec/Hex base switching."""

    # Emitted whenever the On/Off button changes state.
    # True = powered on, False = powered off.
    power_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calculator Interface")
        self.setFixedSize(796, 508)
        self.setStyleSheet("background-color: #c0c0c0;")
        # Remove the OS minimise button — the Calculator is a fixed-size
        # tool window with no menu path back to it once minimised, matching
        # the main window (main_window.py), which hides this button for the
        # same reason.
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinimizeButtonHint)

        # The BebopMain window that owns us — used so the Reset/Step/Run
        # bottom-bar buttons can drive the CPU directly.
        self._host_main = parent

        self.expression = ""
        self.base = "Dec"
        self.memory = [0.0, 0.0, 0.0, 0.0]
        self.powered = False
        self._power_controlled = []  # buttons toggled by On/Off
        self.power_btn = None
        self.leds = []              # populated by _right_panel()
        self._diy_buttons = []       # all DIYButtons in creation order (1-based index)
        self._diy_index = 0          # incremented by _diy() for each button
        self._original_labels = {}   # {button_index: label at creation time}
        self._original_colors = {}   # {button_index: color_index at creation time}
        self._bundled_cache   = None # lazy-loaded packaged Config/defbuttons.ini, see _bundled_defbuttons()

        # Whichever button-def file is "active" -- Apply (from the Configure
        # Button Attributes dialog) and Restore Defaults write to this file.
        # Starts out as the standard Config/defbuttons.ini, but switches to
        # whatever the user picks via Load Button File / Save Button File,
        # so a user's own custom button file keeps receiving their edits
        # instead of everything silently going back to the default file.
        self._active_button_file = _DEFBUTTONS_PATH

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        self._build_display(root)
        self._build_keyboard(root)
        self._build_bottom_bar(root)

        # Load saved button definitions from Config/defbuttons.ini
        self._load_defbuttons()

        # Start in the OFF state
        self._apply_power_state()

    # -- helpers --
    #
    # NOTE: Load Button File / Save Button File / Restore Defaults used to
    # live in a "File" menu on this window's own menu bar. That menu has
    # been removed -- the three commands now live in BebopMain's File menu
    # (see menus.py), which delegates to _load_button_file() /
    # _save_button_file() / _restore_defaults() below via
    # BebopMain._load_button_file() etc. The methods themselves are
    # unchanged, just no longer wired to a local menu.

    def _get_cpu(self):
        """Return the Beboputer CPU, or None if running standalone."""
        return getattr(self._host_main, "cpu", None)

    def _diy(self, label="", color="#000000", bg="#d4d0c8",
              min_w=46, min_h=36, bold=True):
        """Create a DIYButton wired to the Beboputer CPU.

        Each button is assigned a 1-based index and registered in
        ``self._diy_buttons`` so that defbuttons.ini can be applied/saved.
        """
        self._diy_index += 1
        idx = self._diy_index
        self._original_labels[idx] = label
        btn = DIYButton(
            label=label, color=color, bg=bg,
            min_w=min_w, min_h=min_h, bold=bold,
            cpu=self._get_cpu(),
            powered_fn=lambda: self.powered,
            button_index=idx,
            save_fn=self._save_defbutton,
        )
        # Apply label-based defaults for Code and Description.
        # These are overridden by defbuttons.ini if it exists.
        code, desc = _BUTTON_DEFAULTS.get(label, (0x00, "Unassigned"))
        btn._defn.value = code
        btn._defn.description = desc
        self._diy_buttons.append(btn)
        # Snapshot the color this button was actually built with (DIYButton's
        # __init__ already converted the `color` hex param above into
        # btn._defn.color_index) so _restore_defaults() can put buttons back
        # to their real default color instead of guessing/hardcoding one.
        self._original_colors[idx] = btn._defn.color_index
        return btn

    # -- defbuttons.ini -------------------------------------------------------

    def _bundled_defbuttons(self):
        """Load (and cache) the packaged Config/defbuttons.ini via resource_path().

        This is the REAL, complete button configuration -- several
        example .asm programs rely on specific Code= values here for
        buttons that have no Annotation and so aren't covered by
        _BUTTON_DEFAULTS' per-label fallback (e.g. Button 1 has no
        label but Code= $40). Returns {index: ButtonDef}, or {} if the
        packaged file is missing/unparseable (packaging problem) --
        callers must tolerate that and fall back to _BUTTON_DEFAULTS-
        based construction-time values so the app still starts.
        """
        if self._bundled_cache is None:
            try:
                bundled_path = Path(resource_path('Config', 'defbuttons.ini'))
                self._bundled_cache = (
                    load_defbuttons_file(bundled_path) if bundled_path.exists() else {}
                )
            except Exception:
                self._bundled_cache = {}
        return self._bundled_cache

    @staticmethod
    def _clone_button_def(d):
        """Return an independent copy of a ButtonDef.

        _bundled_defbuttons() caches its ButtonDef objects and hands the
        SAME instance out to every caller in a session -- apply_button_def()
        mutates the object it's given (sets bg_color/bold in place) and
        makes it the button's live self._defn, so applying the cached
        instance directly would alias every button that used the same
        cached entry together. Always apply a clone, never the cached
        original.
        """
        c = ButtonDef()
        c.label       = d.label
        c.color_index = d.color_index
        c.bg_color    = d.bg_color
        c.bold        = d.bold
        c.port        = d.port
        c.value       = d.value
        c.description = d.description
        return c

    def _load_defbuttons(self):
        """Apply saved button definitions from the active button file.

        On first run (no per-user file present yet), seeds every button
        from the packaged Config/defbuttons.ini (see _bundled_defbuttons())
        so a fresh install starts with the real shipped configuration --
        not just the partial subset _BUTTON_DEFAULTS covers -- then saves
        that as the new active file so future runs load it normally, the
        same as any other saved button file. Falls back to whatever's
        already on the buttons from construction (_BUTTON_DEFAULTS) only
        if the packaged file itself is unavailable.
        """
        if not self._active_button_file.exists():
            bundled = self._bundled_defbuttons()
            for btn in self._diy_buttons:
                defn = bundled.get(btn._button_index)
                if defn is not None:
                    btn.apply_button_def(self._clone_button_def(defn))
            self._save_all_defbuttons()
            return
        saved = load_defbuttons_file(self._active_button_file)
        for idx, defn in saved.items():
            if 1 <= idx <= len(self._diy_buttons):
                self._diy_buttons[idx - 1].apply_button_def(defn)

    def _save_all_defbuttons(self):
        """Write every button's current definition to the active button file."""
        all_buttons = {btn._button_index: btn._defn for btn in self._diy_buttons}
        save_defbuttons_file(all_buttons, self._active_button_file)

    def _save_defbutton(self, index: int, defn):
        """Persist one button change back to the active button file.

        Loads the current active file, updates the changed entry, then
        saves the whole file so all other buttons are preserved. Writes
        to whichever file is currently active (see
        ``self._active_button_file``) — the default defbuttons.ini unless
        the user has loaded or saved-as a different button file, in which
        case edits keep going to that file instead.
        """
        all_buttons = load_defbuttons_file(self._active_button_file)
        all_buttons[index] = defn
        save_defbuttons_file(all_buttons, self._active_button_file)

    def _load_button_file(self):
        """Let the user pick a .ini file and apply it to all buttons.

        The loaded file becomes the *active* button file: it's applied to
        the on-screen buttons now, and it's what future edits (Apply in
        Configure Button Attributes, Restore Defaults) get written back
        to — not the default defbuttons.ini — until a different file is
        loaded or saved-as.
        """
        dlg = QFileDialog(self, "Load Button File")
        dlg.setOption(QFileDialog.DontUseNativeDialog)
        dlg.setAcceptMode(QFileDialog.AcceptOpen)
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setNameFilters(["DIY Calculator Buttons (*.ini)", "All Files (*)"])
        dlg.setDirectory(str(_BUTTONS_DIR))
        if dlg.exec_() != QFileDialog.Accepted:
            return
        path = dlg.selectedFiles()[0]
        if not path:
            return
        saved = load_defbuttons_file(path)
        for idx, defn in saved.items():
            if 1 <= idx <= len(self._diy_buttons):
                self._diy_buttons[idx - 1].apply_button_def(defn)
        # This file is now the active target for future edits/saves —
        # write it back to itself (not the default defbuttons.ini).
        self._active_button_file = Path(path)
        save_defbuttons_file(saved, self._active_button_file)

    def _save_button_file(self):
        """Save the current button configuration to a user-chosen .ini file.

        Like "Save As" — the chosen file becomes the active button file,
        so subsequent edits keep being written here.
        """
        dlg = QFileDialog(self, "Save Button File")
        dlg.setOption(QFileDialog.DontUseNativeDialog)
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        dlg.setNameFilters(["DIY Calculator Buttons (*.ini)", "All Files (*)"])
        dlg.setDefaultSuffix("ini")
        dlg.setDirectory(str(_BUTTONS_DIR))
        if dlg.exec_() != QFileDialog.Accepted:
            return
        path = dlg.selectedFiles()[0]
        if not path:
            return
        if not path.lower().endswith(".ini"):
            path += ".ini"
        self._active_button_file = Path(path)
        all_buttons = {btn._button_index: btn._defn for btn in self._diy_buttons}
        save_defbuttons_file(all_buttons, self._active_button_file)

    def _restore_defaults(self):
        """Reset every button to its real built-in default Code, Description, and Color.

        Restores each button from the packaged Config/defbuttons.ini (see
        _bundled_defbuttons()) by button index -- the same complete,
        authoritative source _load_defbuttons() seeds a fresh install
        from. This matters beyond cosmetics: several example .asm
        programs depend on exact Code= values for buttons that have no
        Annotation (so _BUTTON_DEFAULTS' per-label lookup can't supply
        them) -- restoring from that incomplete table used to silently
        reset those buttons' codes to $00/"Unassigned", breaking any
        program that relied on them, on top of resetting every color to
        Black. Falls back to _BUTTON_DEFAULTS + each button's real
        construction-time color (self._original_colors) only for a
        button index the packaged file doesn't cover, so this still
        degrades gracefully if packaging is ever broken.
        The restored state is saved to defbuttons.ini.
        """
        bundled = self._bundled_defbuttons()
        for btn in self._diy_buttons:
            idx = btn._button_index
            bundled_defn = bundled.get(idx)
            if bundled_defn is not None:
                btn.apply_button_def(self._clone_button_def(bundled_defn))
                continue
            label = self._original_labels.get(idx, "")
            code, desc = _BUTTON_DEFAULTS.get(label, (0x00, "Unassigned"))
            d             = ButtonDef()
            d.label       = label
            d.value       = code
            d.description = desc
            d.color_index = self._original_colors.get(idx, 0)
            d.bg_color    = btn._defn.bg_color   # preserve visual background
            d.bold        = btn._defn.bold
            btn.apply_button_def(d)
        self._save_all_defbuttons()

    # -- display --

    def _build_display(self, parent):
        self.display = QLineEdit("0")
        self.display.setAlignment(Qt.AlignRight)
        self.display.setReadOnly(True)
        self.display.setMinimumHeight(51)
        self.display.setStyleSheet(_DISPLAY_ON_CSS)
        parent.addWidget(self.display)

    # -- memory row --

    def _build_memory_row(self, parent):
        row = QHBoxLayout()
        row.setSpacing(4)

        self.mem_displays = []
        for _ in range(4):
            dot = QLabel("●")
            dot.setStyleSheet("color: #8b0000; font-size: 16px;")
            dot.setFixedWidth(18)
            row.addWidget(dot)

            me = QLineEdit("0")
            me.setAlignment(Qt.AlignRight)
            me.setFixedWidth(88)
            me.setFixedHeight(29)
            me.setStyleSheet(
                "background:#d4d0c8; border:1px inset #888; font-size:13px;"
            )
            self.mem_displays.append(me)
            row.addWidget(me)

        row.addStretch()

        dot5 = QLabel("●")
        dot5.setStyleSheet("color: #8b0000; font-size: 16px;")
        dot5.setFixedWidth(18)
        row.addWidget(dot5)

        for label in ["Bin", "Dec", "Hex"]:
            b = _calc_make_btn(label, color="#cc0000", min_w=66, min_h=29, bold=True)
            b.clicked.connect(lambda _, l=label: self.set_base(l))
            row.addWidget(b)

        parent.addLayout(row)

    # -- keyboard --

    def _build_keyboard(self, parent):
        # Full-width top strip: LED + button pairs spanning both panels.
        # Pattern: [LED][blank] × 3  then  [LED][Bin]  [LED][Dec]  [LED][Hex]
        parent.addLayout(self._top_led_row())

        kbd = QHBoxLayout()
        kbd.setSpacing(8)
        kbd.addLayout(self._left_panel())
        kbd.addLayout(self._right_panel())
        parent.addLayout(kbd)

    def _top_led_row(self):
        """6 LED+button pairs in one strip spanning both keyboard panels.

        Driven by port $F032: bit 5 = leftmost LED, bit 0 = rightmost.
        LEDs are dull dark red when off, bright red when on.
        """
        row = QHBoxLayout()
        row.setSpacing(3)

        labels = ["", "", "", "Bin", "Dec", "Hex"]
        for lbl in labels:
            led = QLabel()
            led.setStyleSheet(_LED_OFF_CSS)
            row.addWidget(led)
            self.leds.append(led)

            if lbl in ("Bin", "Dec", "Hex"):
                b = self._diy(lbl, color="#cc0000", bold=True)
            else:
                b = self._diy("")
            row.addWidget(b)

        return row

    def _left_panel(self):
        grid = QGridLayout()
        grid.setSpacing(3)

        for r in range(5):
            for c in range(4):
                btn = self._diy("", min_w=36, min_h=36)
                btn.setFixedSize(40, 40)
                grid.addWidget(btn, r, c)

        for r, lbl in enumerate(["Sin", "Cos", "Tan", "Log", "n!"]):
            btn = self._diy(lbl, color="#cc00cc", min_w=46, min_h=36)
            btn.setFixedSize(51, 40)
            grid.addWidget(btn, r, 4)

        for r, lbl in enumerate(["x^y", "x^3", "x^2", "Rx", "1/x"]):
            btn = self._diy(lbl, color="#cc00cc", min_w=46, min_h=36)
            btn.setFixedSize(51, 40)
            grid.addWidget(btn, r, 5)

        return grid

    def _right_panel(self):
        grid = QGridLayout()
        grid.setSpacing(3)

        rows = [
            [("7","#000"),("8","#000"),("9","#000"),("/","#000"),("Mod","#000"),("Exp","#000")],
            [("4","#000"),("5","#000"),("6","#000"),("*","#000"),("Pi","#000"),("F-S","#000")],
            [("1","#000"),("2","#000"),("3","#000"),("--","#000"),("(","#000"),(")","#000")],
        ]
        for r, row in enumerate(rows):
            for c, (lbl, col) in enumerate(row):
                btn = self._diy(lbl, color=col, min_w=52, min_h=36)
                btn.setFixedSize(58, 40)
                grid.addWidget(btn, r, c)

        for c, lbl in enumerate(["0", "+/-", ".", "+", "="]):
            btn = self._diy(lbl, min_w=52, min_h=36)
            btn.setFixedSize(58, 40)
            grid.addWidget(btn, 3, c)

        for c, lbl in enumerate(list("ABCDEF")):
            btn = self._diy(lbl, min_w=52, min_h=36)
            btn.setFixedSize(58, 40)
            grid.addWidget(btn, 4, c)

        return grid

    # -- bottom bar --

    def _build_bottom_bar(self, parent):
        bar = QHBoxLayout()
        bar.setSpacing(4)

        _bottom_bar_tooltips = {
            "On/Off": "Turn the calculator on or off",
            "Reset":  "Reset the CPU and return to idle",
            "Step":   "Execute a single CPU instruction",
            "Run":    "Run the CPU until it HALTs or hits a breakpoint",
        }
        for lbl in ["On/Off", "Reset", "Step", "Run"]:
            b = _calc_make_btn(lbl, min_w=77, min_h=40, tooltip=_bottom_bar_tooltips[lbl])
            b.setFixedSize(77, 40)
            b.clicked.connect(lambda _, l=lbl: self.control(l))
            bar.addWidget(b)
            if lbl in ("Reset", "Step", "Run"):
                self._power_controlled.append(b)
            elif lbl == "On/Off":
                self.power_btn = b

        bar.addStretch()

        for lbl in ["Clear", "CE", "Back", "Enter"]:
            btn = self._diy(lbl, color="#cc0000", min_w=77, min_h=40, bold=True)
            btn.setFixedSize(77, 40)
            btn.setToolTip(_BUTTON_DEFAULTS.get(lbl, (0x00, "Unassigned"))[1])
            bar.addWidget(btn)

        parent.addLayout(bar)

    # -- power state --

    def _apply_power_state(self):
        """Enable/disable power-controlled buttons and update display style."""
        for btn in self._power_controlled:
            btn.setEnabled(self.powered)

        if self.powered:
            self.display.setStyleSheet(_DISPLAY_ON_CSS)
            # Boot sequence: write 24 dashes to port $F031.
            # expression is already cleared by control() before we get here,
            # so write_display appends directly onto a blank slate.
            for _ in range(24):
                self.write_display(ord('-'))   # 0x2D via $F031
            # Light up the top-row LEDs as part of power-on, same as real
            # hardware would (the indicator LEDs come alive with the board,
            # independent of whatever a loaded program later does with them
            # via port $F032/write_leds()).
            for led in self.leds:
                led.setStyleSheet(_LED_ON_CSS)
        else:
            self.display.setStyleSheet(_DISPLAY_OFF_CSS)
            self.display.setText("")
            for led in self.leds:
                led.setStyleSheet(_LED_OFF_CSS)

        if self.power_btn is not None:
            self.power_btn.setStyleSheet(
                _POWER_BTN_ON_CSS if self.powered else _POWER_BTN_OFF_CSS
            )

    # -- logic --

    def _refresh(self, text=None):
        self.display.setText(text if text is not None else (self.expression or "0"))

    def blank_display(self):
        """Clear the display to truly empty, not "0".

        Used by CPU Reset: real hardware doesn't know to show "0" until a
        program actually writes something -- showing "0" would be lying
        about there being an initialized program driving the display.
        write_display()'s CLR-code handling ($0D/$10/$1B) also blanks to
        empty now, for the same reason: a program clearing its own
        display (e.g. lab2a writing $10) hasn't displayed a "0" value,
        it's cleared the screen.
        """
        self.expression = ""
        self.display.setText("")

    def show_dash_display(self):
        """Show the boot-style dash placeholder ('------------------------').

        Used when a program is loaded into RAM (File > Load ROM/RAM):
        real hardware doesn't know what to show until the freshly-loaded
        program actually drives the display via port $F031, so it shows
        the same 24-dash placeholder as power-on rather than going fully
        blank (which would look broken) or showing "0" (which would
        misleadingly imply a program had already initialized it).
        No-op if the calculator is powered off.
        """
        self.expression = ""
        for _ in range(24):
            self.write_display(ord('-'))   # 0x2D via $F031

    # -- memory-mapped display port $F031 -------------------------------------

    def write_display(self, ch: int):
        """Receive one byte from port $F031 and update the display.

        Printable ASCII (32-126) is appended to the expression.
        Raw digit codes $00-$09 are displayed as '0'-'9'.
        $0D (CR), $10, or $1B (ESC) clears the display.
        All other values are ignored.
        Silently discarded when the calculator is powered off.
        """
        if not self.powered:
            return
        if 32 <= ch <= 126:
            self.expression += chr(ch)
            self._refresh()
        elif 0x00 <= ch <= 0x09:
            self.expression += str(ch)
            self._refresh()
        elif 0x0A <= ch <= 0x0F:
            self.expression += chr(ch - 0x0A + ord('A'))  # raw A-F → 'A'-'F'
            self._refresh()
        elif ch in (0x0D, 0x10, 0x1B):
            # Clear the display to truly empty, not "0" -- a CLR code is
            # a program actively clearing the screen (e.g. lab2a writing
            # $10), and showing "0" would misrepresent that as a value
            # being displayed. Real hardware just goes blank.
            self.expression = ""
            self._refresh("")

    def write_leds(self, byte: int):
        """Set the 6 LED indicators from port $F032.

        Bit 5 drives the leftmost LED, bit 0 the rightmost.
        Silently discarded when the calculator is powered off.
        """
        if not self.powered:
            return
        for i, led in enumerate(self.leds):
            on = bool((byte >> (5 - i)) & 1)
            led.setStyleSheet(_LED_ON_CSS if on else _LED_OFF_CSS)

    def key_press(self, key):
        mapping = {"--": "-", "Mod": "%", "Exp": "e+", "Pi": str(math.pi)}
        self.expression += mapping.get(key, key)
        self._refresh()

    def evaluate(self):
        try:
            result = eval(self.expression.replace("^", "**"))
            if self.base == "Bin":
                txt = bin(int(result))
            elif self.base == "Hex":
                txt = hex(int(result)).upper()
            else:
                txt = str(result)
            self.expression = str(result)
            self._refresh(txt)
        except Exception:
            self._refresh("Error")
            self.expression = ""

    def trig_op(self, op):
        try:
            val = float(eval(self.expression)) if self.expression else 0.0
            ops = {
                "Sin": math.sin,
                "Cos": math.cos,
                "Tan": math.tan,
                "Log": math.log10,
                "n!":  lambda v: float(math.factorial(int(v))),
            }
            result = ops[op](val)
            self.expression = str(result)
            self._refresh(str(result))
        except Exception:
            self._refresh("Error")
            self.expression = ""

    def func_op(self, op):
        try:
            val = float(eval(self.expression)) if self.expression else 0.0
            if op == "x^y":
                self.expression += "**"
                self._refresh()
                return
            result = {
                "x^3": val ** 3,
                "x^2": val ** 2,
                "Rx":  math.sqrt(val),
                "1/x": 1.0 / val,
            }[op]
            self.expression = str(result)
            self._refresh(str(result))
        except Exception:
            self._refresh("Error")
            self.expression = ""

    def set_base(self, base):
        self.base = base
        try:
            val = int(float(eval(self.expression))) if self.expression else 0
            if base == "Bin":
                self._refresh(bin(val))
            elif base == "Hex":
                self._refresh(hex(val).upper())
            else:
                self._refresh(str(val))
        except Exception:
            pass

    def control(self, cmd):
        if cmd == "On/Off":
            self.powered = not self.powered
            self.expression = ""
            self._apply_power_state()
            self.power_changed.emit(self.powered)
            return

        if cmd in ("Run", "Step", "Reset") and not self.powered:
            return

        if cmd in ("Reset", "Step", "Run"):
            self._drive_host(cmd)
            if cmd == "Reset":
                # The 6 indicator LEDs are always on by default -- same
                # as the power-on boot state -- and only go dark when a
                # running program explicitly clears bits via port $F032
                # (write_leds()). Reset returns the board to idle with
                # no program driving anything, so the LEDs should come
                # back on too, not go dark.
                for led in self.leds:
                    led.setStyleSheet(_LED_ON_CSS)
            return

        if cmd in ("Clear", "CE"):
            self.expression = ""
            self._refresh("0")
        elif cmd == "Back":
            self.expression = self.expression[:-1]
            self._refresh()
        elif cmd == "Enter":
            self.evaluate()

    def closeEvent(self, event):
        """Prevent the calculator window from being closed."""
        event.ignore()

    def changeEvent(self, event):
        """Undo minimizing immediately.

        The WindowMinimizeButtonHint stripped in __init__ only hides the
        title-bar button — it doesn't stop a Linux window manager from
        minimizing this window some other way (a keyboard shortcut, the
        window's system menu, "show desktop", a taskbar entry, etc.). On
        Windows this is largely moot, but several Linux WMs honour those
        paths regardless of the hint. Since this is a standalone tool
        window with no menu item to reopen it once minimized, that would
        leave it an orphaned, inaccessible window with no way back — so
        any minimize is reversed the moment it happens.
        """
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
                self.show()
                self.raise_()
                self.activateWindow()

    def _drive_host(self, cmd):
        """Forward Reset / Step / Run to the parent BebopMain window."""
        host = self._host_main
        if host is None:
            return
        slot = {
            "Reset": getattr(host, "_do_reset", None),
            "Step":  getattr(host, "_do_step",  None),
            "Run":   getattr(host, "_do_run",   None),
        }.get(cmd)
        if callable(slot):
            slot()
