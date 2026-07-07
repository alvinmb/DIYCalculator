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

from PyQt5.QtCore import Qt, QSize, pyqtSignal
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


# -- Default button Code + Description ----------------------------------------
# Maps button label → (hex_code, description).
# Code is the byte written to port $F011 on left-click.
# x^2 = $3D matches the reference screenshot.

_BUTTON_DEFAULTS = {
    # base-mode switches
    "Bin":  (0x02, "Switch to binary mode"),
    "Dec":  (0x0A, "Switch to decimal mode"),
    "Hex":  (0x10, "Switch to hexadecimal mode"),
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


def _calc_make_btn(text, color="#000000", bg="#d4d0c8", min_w=46, min_h=36, bold=False):
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
    """)
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

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        self._build_menu_bar()
        self._build_display(root)
        self._build_keyboard(root)
        self._build_bottom_bar(root)

        # Load saved button definitions from Config/defbuttons.ini
        self._load_defbuttons()

        # Start in the OFF state
        self._apply_power_state()

    # -- menu bar --

    def _build_menu_bar(self):
        """Add the File menu with Load Button File and Restore Defaults."""
        file_menu = self.menuBar().addMenu("File")

        load_act = file_menu.addAction("Load Button File...")
        load_act.triggered.connect(self._load_button_file)

        save_act = file_menu.addAction("Save Button File...")
        save_act.triggered.connect(self._save_button_file)

        restore_act = file_menu.addAction("Restore Defaults")
        restore_act.triggered.connect(self._restore_defaults)

    # -- helpers --

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
        return btn

    # -- defbuttons.ini -------------------------------------------------------

    def _load_defbuttons(self):
        """Apply saved button definitions from Config/defbuttons.ini.

        On first run (no file present), seeds defbuttons.ini from the
        built-in ``_BUTTON_DEFAULTS`` table so the user starts with a
        fully populated default configuration.
        """
        if not _DEFBUTTONS_PATH.exists():
            # First run — write defaults to disk so future sessions load them.
            self._save_all_defbuttons()
            return
        saved = load_defbuttons_file()
        for idx, defn in saved.items():
            if 1 <= idx <= len(self._diy_buttons):
                self._diy_buttons[idx - 1].apply_button_def(defn)

    def _save_all_defbuttons(self):
        """Write every button's current definition to defbuttons.ini."""
        all_buttons = {btn._button_index: btn._defn for btn in self._diy_buttons}
        save_defbuttons_file(all_buttons)

    def _save_defbutton(self, index: int, defn):
        """Persist one button change back to Config/defbuttons.ini.

        Loads the current file, updates the changed entry, then saves
        the whole file so all other buttons are preserved.
        """
        all_buttons = load_defbuttons_file()
        all_buttons[index] = defn
        save_defbuttons_file(all_buttons)

    def _load_button_file(self):
        """Let the user pick a .ini file and apply it to all buttons.

        The loaded file replaces the active button configuration and is
        saved as the new defbuttons.ini so it persists across sessions.
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
        # Persist as the new defbuttons.ini
        save_defbuttons_file(saved)

    def _save_button_file(self):
        """Save the current button configuration to a user-chosen .ini file."""
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
        all_buttons = {btn._button_index: btn._defn for btn in self._diy_buttons}
        save_defbuttons_file(all_buttons, path)

    def _restore_defaults(self):
        """Reset every button to its built-in default Code and Description.

        Labels, colors, and codes are all restored to the values defined
        in ``_BUTTON_DEFAULTS`` (keyed by the original label at creation).
        The restored state is saved to defbuttons.ini.
        """
        for btn in self._diy_buttons:
            idx   = btn._button_index
            label = self._original_labels.get(idx, "")
            code, desc = _BUTTON_DEFAULTS.get(label, (0x00, "Unassigned"))
            d             = ButtonDef()
            d.label       = label
            d.value       = code
            d.description = desc
            d.color_index = 0             # Black
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

        for lbl in ["On/Off", "Reset", "Step", "Run"]:
            b = _calc_make_btn(lbl, min_w=77, min_h=40)
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
            self.expression = ""
            self._refresh("0")

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
