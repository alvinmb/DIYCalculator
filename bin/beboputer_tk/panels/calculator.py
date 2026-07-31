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

"""Classic-style scientific Calculator -- tkinter port of
beboputer_v7/tools/calculator.py.

Behavioral parity with the Qt version:
  - The display is driven ONLY by port $F031 (write_display) and the 6
    LEDs ONLY by port $F032 (write_leds) -- both wired as CPU write
    hooks by main_window.py, same as the Qt build. Every calculator key
    (digits, operators, Sin/Cos/..., Clear/CE/Back/Enter) is a DIYButton
    that writes its configured code to $F011; the CPU-resident program
    is what actually drives the display back via $F031. The calculator
    widget itself has NO built-in expression evaluator -- and neither
    does the Qt version's `.control()`/`.key_press()`/`.evaluate()`
    machinery, once you trace it: those methods are never connected to
    anything (the DIY buttons that share their names -- Clear, CE,
    Back, Enter -- write to the CPU port like every other button, they
    don't call `.control()`). That dead code is intentionally NOT
    ported here.
  - On/Off, Reset, Step, Run at the bottom are real host-driven
    controls (regular buttons, not DIYButtons) -- same as Qt.
  - defbuttons.ini loading/saving/Configure-Button-Attributes/Restore
    Defaults logic is ported faithfully, reusing the same Qt-free
    ButtonDef/load_defbuttons_file/save_defbuttons_file helpers the Qt
    build uses (beboputer_v7.tools.diy_button).

NOT ported (confirmed dead in the Qt source -- see module docstring
above): the memory-row widget (_build_memory_row is defined but never
called even in the Qt file) and the built-in expression
evaluator/`.control()`'s Clear/CE/Back/Enter branch.
"""

from __future__ import annotations

import math
from pathlib import Path

import tkinter as tk
from tkinter import filedialog

from .diy_button import (
    DIYButton, ButtonDef,
    load_defbuttons_file, save_defbuttons_file,
    _DEFBUTTONS_PATH, _BUTTONS_DIR,
)

try:
    from beboputer_v7.paths import resource_path
except ImportError:  # pragma: no cover
    def resource_path(*parts):
        return str(Path(*parts))


# -- Default button Code + Description, copied verbatim from
#    beboputer_v7/tools/calculator.py so a fresh install without a
#    defbuttons.ini yet still gets sane per-label defaults. ------------------

_BUTTON_DEFAULTS = {
    "Bin":  (0x43, "Switch to binary mode"),
    "Dec":  (0x44, "Switch to decimal mode"),
    "Hex":  (0x45, "Switch to hexadecimal mode"),
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
    "+":    (0x2B, "Add"),
    "--":   (0x2D, "Negate"),
    "*":    (0x2A, "Multiply"),
    "/":    (0x2F, "Divide"),
    "=":    (0x3D, "Equals / evaluate"),
    ".":    (0x2E, "Decimal point"),
    "+/-":  (0x4E, "Change sign"),
    "(":    (0x28, "Open parenthesis"),
    ")":    (0x29, "Close parenthesis"),
    "Mod":  (0x4D, "Modulo"),
    "Exp":  (0x45, "Exponent notation"),
    "Pi":   (0x50, "Pi constant"),
    "F-S":  (0x46, "Float / scientific toggle"),
    "A":    (0x41, "Hex digit A"),
    "B":    (0x42, "Hex digit B"),
    "C":    (0x43, "Hex digit C"),
    "D":    (0x44, "Hex digit D"),
    "E":    (0x45, "Hex digit E"),
    "F":    (0x46, "Hex digit F"),
    "Clear": (0x1B, "Clear display"),
    "CE":   (0x7F, "Clear entry"),
    "Back": (0x08, "Backspace"),
    "Enter": (0x0D, "Evaluate expression"),
}

_DISPLAY_ON_BG, _DISPLAY_ON_FG = "#c8f0c8", "#000000"
_DISPLAY_OFF_BG, _DISPLAY_OFF_FG = "#6e7a6e", "#4a504a"
_LED_OFF, _LED_ON = "#3a0000", "#ff1a1a"
_POWER_ON_BG, _POWER_OFF_BG = "#7ed07e", "#d4d0c8"


class Calculator(tk.Frame):
    """Classic-style scientific calculator with Bin/Dec/Hex base switching."""

    def __init__(self, parent, host_main=None, **kwargs):
        super().__init__(parent, bg="#c0c0c0", **kwargs)
        # The BebopMain window that owns us -- used so Reset/Step/Run
        # drive the CPU directly, same relationship as the Qt version's
        # self._host_main / self._get_cpu() / self._drive_host().
        self._host_main = host_main

        self.expression = ""
        self.base = "Dec"
        self.powered = False
        self._power_controlled = []   # buttons toggled by On/Off
        self.power_btn = None
        self.leds = []
        self._diy_buttons = []
        self._diy_index = 0
        self._original_labels = {}
        self._original_colors = {}
        self._bundled_cache = None

        # Whichever button-def file is "active" -- Apply / Restore Defaults
        # write to this file. Starts as the standard defbuttons.ini, but
        # switches to whatever the user Load/Save-As's, same as Qt.
        self._active_button_file = _DEFBUTTONS_PATH

        self._build_display()
        self._build_keyboard()
        self._build_bottom_bar()

        self._load_defbuttons()
        self._apply_power_state()

    # -- CPU access -------------------------------------------------------

    def _get_cpu(self):
        return getattr(self._host_main, "cpu", None)

    def _diy(self, parent, label="", color="#000000", bg="#d4d0c8",
             min_w=46, min_h=36, bold=True):
        self._diy_index += 1
        idx = self._diy_index
        self._original_labels[idx] = label
        btn = DIYButton(
            parent, label=label, color=color, bg=bg,
            min_w=min_w, min_h=min_h, bold=bold,
            cpu=self._get_cpu(),
            powered_fn=lambda: self.powered,
            button_index=idx,
            save_fn=self._save_defbutton,
        )
        code, desc = _BUTTON_DEFAULTS.get(label, (0x00, "Unassigned"))
        btn._defn.value = code
        btn._defn.description = desc
        self._diy_buttons.append(btn)
        self._original_colors[idx] = btn._defn.color_index
        return btn

    # -- defbuttons.ini -----------------------------------------------------

    def _bundled_defbuttons(self):
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
        c = ButtonDef()
        c.label = d.label
        c.color_index = d.color_index
        c.bg_color = d.bg_color
        c.bold = d.bold
        c.port = d.port
        c.value = d.value
        c.description = d.description
        return c

    def _load_defbuttons(self):
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
        all_buttons = {btn._button_index: btn._defn for btn in self._diy_buttons}
        save_defbuttons_file(all_buttons, self._active_button_file)

    def _save_defbutton(self, index: int, defn):
        all_buttons = load_defbuttons_file(self._active_button_file)
        all_buttons[index] = defn
        save_defbuttons_file(all_buttons, self._active_button_file)

    def _load_button_file(self):
        path = filedialog.askopenfilename(
            title="Load Button File", initialdir=str(_BUTTONS_DIR),
            filetypes=[("DIY Calculator Buttons", "*.ini"), ("All files", "*.*")],
        )
        if not path:
            return
        saved = load_defbuttons_file(path)
        for idx, defn in saved.items():
            if 1 <= idx <= len(self._diy_buttons):
                self._diy_buttons[idx - 1].apply_button_def(defn)
        self._active_button_file = Path(path)
        save_defbuttons_file(saved, self._active_button_file)

    def _save_button_file(self):
        path = filedialog.asksaveasfilename(
            title="Save Button File", initialdir=str(_BUTTONS_DIR),
            defaultextension=".ini",
            filetypes=[("DIY Calculator Buttons", "*.ini"), ("All files", "*.*")],
        )
        if not path:
            return
        self._active_button_file = Path(path)
        all_buttons = {btn._button_index: btn._defn for btn in self._diy_buttons}
        save_defbuttons_file(all_buttons, self._active_button_file)

    def _restore_defaults(self):
        bundled = self._bundled_defbuttons()
        for btn in self._diy_buttons:
            idx = btn._button_index
            bundled_defn = bundled.get(idx)
            if bundled_defn is not None:
                btn.apply_button_def(self._clone_button_def(bundled_defn))
                continue
            label = self._original_labels.get(idx, "")
            code, desc = _BUTTON_DEFAULTS.get(label, (0x00, "Unassigned"))
            d = ButtonDef()
            d.label = label
            d.value = code
            d.description = desc
            d.color_index = self._original_colors.get(idx, 0)
            d.bg_color = btn._defn.bg_color
            d.bold = btn._defn.bold
            btn.apply_button_def(d)
        self._save_all_defbuttons()

    # -- display --------------------------------------------------------------

    def _build_display(self):
        self.display = tk.Entry(
            self, justify="right", state="readonly",
            font=("Courier New", 21, "bold"),
            readonlybackground=_DISPLAY_ON_BG, fg=_DISPLAY_ON_FG,
            relief="sunken", bd=3,
        )
        self.display.pack(fill="x", padx=6, pady=(6, 4))
        self._set_display_text("0")

    def _set_display_text(self, text):
        self.display.configure(state="normal")
        self.display.delete(0, "end")
        self.display.insert(0, text)
        self.display.configure(state="readonly")

    # -- keyboard ---------------------------------------------------------

    def _build_keyboard(self):
        self._top_led_row()

        kbd = tk.Frame(self, bg="#c0c0c0")
        kbd.pack(fill="both", expand=True, padx=6, pady=2)
        left = tk.Frame(kbd, bg="#c0c0c0")
        left.pack(side="left", padx=(0, 6))
        right = tk.Frame(kbd, bg="#c0c0c0")
        right.pack(side="left")

        self._left_panel(left)
        self._right_panel(right)

    def _top_led_row(self):
        """6 LED+button pairs in one strip, port $F032 driven.

        Bit 5 = leftmost LED, bit 0 = rightmost.
        """
        row = tk.Frame(self, bg="#c0c0c0")
        row.pack(fill="x", padx=6, pady=(0, 2))

        labels = ["", "", "", "Bin", "Dec", "Hex"]
        for lbl in labels:
            led = tk.Label(
                row, bg=_LED_OFF, width=2, height=1,
                relief="sunken", bd=1,
            )
            led.pack(side="left", padx=2)
            self.leds.append(led)

            if lbl in ("Bin", "Dec", "Hex"):
                b = self._diy(row, lbl, color="#cc0000", bold=True)
            else:
                b = self._diy(row, "")
            b.pack(side="left", padx=(0, 6))

    def _left_panel(self, parent):
        grid = tk.Frame(parent, bg="#c0c0c0")
        grid.pack()

        for r in range(5):
            for c in range(4):
                btn = self._diy(grid, "", min_w=36, min_h=36)
                btn.grid(row=r, column=c, padx=2, pady=2)

        for r, lbl in enumerate(["Sin", "Cos", "Tan", "Log", "n!"]):
            btn = self._diy(grid, lbl, color="#cc00cc", min_w=46, min_h=36)
            btn.grid(row=r, column=4, padx=2, pady=2)

        for r, lbl in enumerate(["x^y", "x^3", "x^2", "Rx", "1/x"]):
            btn = self._diy(grid, lbl, color="#cc00cc", min_w=46, min_h=36)
            btn.grid(row=r, column=5, padx=2, pady=2)

    def _right_panel(self, parent):
        grid = tk.Frame(parent, bg="#c0c0c0")
        grid.pack()

        rows = [
            ["7", "8", "9", "/", "Mod", "Exp"],
            ["4", "5", "6", "*", "Pi", "F-S"],
            ["1", "2", "3", "--", "(", ")"],
        ]
        for r, row in enumerate(rows):
            for c, lbl in enumerate(row):
                btn = self._diy(grid, lbl, color="#000000", min_w=52, min_h=36)
                btn.grid(row=r, column=c, padx=2, pady=2)

        for c, lbl in enumerate(["0", "+/-", ".", "+", "="]):
            btn = self._diy(grid, lbl, min_w=52, min_h=36)
            btn.grid(row=3, column=c, padx=2, pady=2)

        for c, lbl in enumerate(list("ABCDEF")):
            btn = self._diy(grid, lbl, min_w=52, min_h=36)
            btn.grid(row=4, column=c, padx=2, pady=2)

    # -- bottom bar ---------------------------------------------------------

    def _build_bottom_bar(self):
        bar = tk.Frame(self, bg="#c0c0c0")
        bar.pack(fill="x", padx=6, pady=(2, 6))

        tooltips = {
            "On/Off": "Turn the calculator on or off",
            "Reset": "Reset the CPU and return to idle",
            "Step": "Execute a single CPU instruction",
            "Run": "Run the CPU until it HALTs or hits a breakpoint",
        }
        for lbl in ["On/Off", "Reset", "Step", "Run"]:
            b = tk.Button(
                bar, text=lbl, font=("Arial", 13, "bold"),
                bg=_POWER_OFF_BG, relief="raised", bd=2, width=8, height=2,
                command=lambda l=lbl: self.control(l),
            )
            b.pack(side="left", padx=2)
            if lbl in ("Reset", "Step", "Run"):
                b.configure(state="disabled")
                self._power_controlled.append(b)
            elif lbl == "On/Off":
                self.power_btn = b
            self._add_tooltip(b, tooltips[lbl])

        spacer = tk.Frame(bar, bg="#c0c0c0")
        spacer.pack(side="left", fill="x", expand=True)

        for lbl in ["Clear", "CE", "Back", "Enter"]:
            btn = self._diy(bar, lbl, color="#cc0000", min_w=77, min_h=40, bold=True)
            btn.pack(side="left", padx=2)

    @staticmethod
    def _add_tooltip(widget, text):
        """Minimal tooltip -- no tkinter built-in, unlike Qt's setToolTip()."""
        tip = {"win": None}

        def _show(event):
            if tip["win"] is not None:
                return
            x = widget.winfo_rootx() + 10
            y = widget.winfo_rooty() + widget.winfo_height() + 6
            win = tk.Toplevel(widget)
            win.wm_overrideredirect(True)
            win.wm_geometry(f"+{x}+{y}")
            tk.Label(
                win, text=text, bg="#ffffcc", fg="#000000",
                relief="solid", bd=1, font=("Arial", 11), padx=4, pady=2,
            ).pack()
            tip["win"] = win

        def _hide(event):
            if tip["win"] is not None:
                tip["win"].destroy()
                tip["win"] = None

        widget.bind("<Enter>", _show)
        widget.bind("<Leave>", _hide)

    # -- power state ----------------------------------------------------------

    def _apply_power_state(self):
        for btn in self._power_controlled:
            btn.configure(state="normal" if self.powered else "disabled")

        if self.powered:
            self.display.configure(readonlybackground=_DISPLAY_ON_BG, fg=_DISPLAY_ON_FG)
            for _ in range(24):
                self.write_display(ord('-'))
            for led in self.leds:
                led.configure(bg=_LED_ON)
        else:
            self.display.configure(readonlybackground=_DISPLAY_OFF_BG, fg=_DISPLAY_OFF_FG)
            self.expression = ""
            self._set_display_text("")
            for led in self.leds:
                led.configure(bg=_LED_OFF)

        if self.power_btn is not None:
            self.power_btn.configure(bg=_POWER_ON_BG if self.powered else _POWER_OFF_BG)

    # -- logic ------------------------------------------------------------

    def _refresh(self, text=None):
        self._set_display_text(text if text is not None else (self.expression or "0"))

    def blank_display(self):
        """Clear to truly empty, not "0" -- see calculator.py's docstring
        for why (Reset means no program is driving the display yet)."""
        self.expression = ""
        self._set_display_text("")

    def show_dash_display(self):
        """Boot-style dash placeholder, shown on program load."""
        self.expression = ""
        for _ in range(24):
            self.write_display(ord('-'))

    # -- memory-mapped display port $F031 --------------------------------

    def write_display(self, ch: int):
        """Receive one byte from port $F031 and update the display."""
        if not self.powered:
            return
        if 32 <= ch <= 126:
            self.expression += chr(ch)
            self._refresh()
        elif 0x00 <= ch <= 0x09:
            self.expression += str(ch)
            self._refresh()
        elif 0x0A <= ch <= 0x0F:
            self.expression += chr(ch - 0x0A + ord('A'))
            self._refresh()
        elif ch in (0x0D, 0x10, 0x1B):
            self.expression = ""
            self._refresh("")

    def write_leds(self, byte: int):
        """Set the 6 LED indicators from port $F032."""
        if not self.powered:
            return
        for i, led in enumerate(self.leds):
            on = bool((byte >> (5 - i)) & 1)
            led.configure(bg=_LED_ON if on else _LED_OFF)

    def control(self, cmd):
        if cmd == "On/Off":
            self.powered = not self.powered
            self.expression = ""
            self._apply_power_state()
            if self._host_main is not None:
                on_power = getattr(self._host_main, "_on_power_changed", None)
                if callable(on_power):
                    on_power(self.powered)
            return

        if cmd in ("Run", "Step", "Reset") and not self.powered:
            return

        if cmd in ("Reset", "Step", "Run"):
            self._drive_host(cmd)
            if cmd == "Reset":
                for led in self.leds:
                    led.configure(bg=_LED_ON)
            return

    def _drive_host(self, cmd):
        host = self._host_main
        if host is None:
            return
        slot = {
            "Reset": getattr(host, "_do_reset", None),
            "Step": getattr(host, "_do_step", None),
            "Run": getattr(host, "_do_run", None),
        }.get(cmd)
        if callable(slot):
            slot()
