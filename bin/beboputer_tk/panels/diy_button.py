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

"""DIY Calculator Button -- tkinter port of beboputer_v7/tools/diy_button.py.

Left-click writes defn.value to port $F011 via the CPU (no ASCII-nibble
translation -- see the comment in _execute(), this session already found
and fixed the bug that translation caused in the Qt build).
Right-click opens Configure Button Attributes (only when calc is off).

The file-format helpers (ButtonDef, load_defbuttons_file,
save_defbuttons_file, COLORS, _color_index, _parse_code, _DEFBUTTONS_PATH,
_BUTTONS_DIR) have zero Qt dependency -- they're configparser/pathlib only
-- so this module imports and reuses them directly from
beboputer_v7.tools.diy_button instead of duplicating them. Only the two
Qt *widgets* in that module (DIYButton itself, ConfigureButtonAttributes)
need a tkinter-native replacement, which is what this file provides.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from beboputer_v7.tools.diy_button import (
    ButtonDef, COLORS, _color_index, _parse_code,
    load_defbuttons_file, save_defbuttons_file,
    _DEFBUTTONS_PATH, _BUTTONS_DIR,
)

_FIXED_PORT = 0xF011
_BTN_BG = "#d4d0c8"


class ConfigureButtonAttributes(tk.Toplevel):
    """Right-click dialog: edit Code / Annotation / Color / Description.

    Apply calls back with a new ButtonDef; the caller (DIYButton) applies
    it to itself and persists it via save_fn, mirroring the Qt dialog's
    get_defn() + caller-applies pattern.
    """

    def __init__(self, parent, defn: ButtonDef, on_apply):
        super().__init__(parent)
        self.title("Configure Button Attributes")
        self.resizable(False, False)
        self.configure(bg="#c0c0c0")
        self._defn = defn
        self._on_apply = on_apply
        self._build()
        self.transient(parent)
        self.grab_set()

    def _build(self):
        frm = tk.Frame(self, bg="#c0c0c0", padx=14, pady=12)
        frm.pack(fill="both", expand=True)
        F = ("Arial", 11, "bold")
        FIELD = ("Arial", 11)

        tk.Label(frm, text="Code:", font=F, bg="#c0c0c0").grid(
            row=0, column=0, sticky="e", pady=5, padx=(0, 8))
        self.code_var = tk.StringVar(value=f"${self._defn.value:02X}")
        tk.Entry(frm, textvariable=self.code_var, width=10, font=FIELD).grid(
            row=0, column=1, sticky="w", pady=5)

        tk.Label(frm, text="Annotation:", font=F, bg="#c0c0c0").grid(
            row=1, column=0, sticky="e", pady=5, padx=(0, 8))
        self.annot_var = tk.StringVar(value=self._defn.label)
        tk.Entry(frm, textvariable=self.annot_var, width=22, font=FIELD).grid(
            row=1, column=1, sticky="w", pady=5)

        tk.Label(frm, text="Color:", font=F, bg="#c0c0c0").grid(
            row=2, column=0, sticky="e", pady=5, padx=(0, 8))
        self.color_var = tk.StringVar(value=COLORS[self._defn.color_index][0])
        ttk.Combobox(
            frm, textvariable=self.color_var, values=[c[0] for c in COLORS],
            state="readonly", width=19, font=FIELD,
        ).grid(row=2, column=1, sticky="w", pady=5)

        tk.Label(frm, text="Description:", font=F, bg="#c0c0c0").grid(
            row=3, column=0, sticky="e", pady=5, padx=(0, 8))
        self.desc_var = tk.StringVar(value=self._defn.description)
        tk.Entry(frm, textvariable=self.desc_var, width=22, font=FIELD).grid(
            row=3, column=1, sticky="w", pady=5)

        btn_row = tk.Frame(frm, bg="#c0c0c0")
        btn_row.grid(row=4, column=0, columnspan=2, sticky="e", pady=(12, 0))
        tk.Button(
            btn_row, text="Apply", font=F, width=9,
            command=self._apply,
        ).pack(side="right")

    def _apply(self):
        d = ButtonDef()
        d.label = self.annot_var.get().strip()
        d.color_index = _color_index(self.color_var.get())
        d.bold = self._defn.bold
        d.bg_color = self._defn.bg_color
        d.value = _parse_code(self.code_var.get())
        d.description = self.desc_var.get().strip() or "Unassigned"
        self.destroy()
        self._on_apply(d)


class DIYButton(tk.Button):
    """A calculator button with an editable ButtonDef.

    Left-click  -- writes defn.value to port $F011 via the CPU.
    Right-click -- opens Configure Button Attributes (only when calc is off).

    Parameters mirror the Qt DIYButton constructor.
    """

    def __init__(self, parent, label="", color="#000000", bg=_BTN_BG,
                 min_w=46, min_h=36, bold=False, cpu=None,
                 powered_fn=None, button_index=0, save_fn=None, **kwargs):
        self._cpu = cpu
        self._powered_fn = powered_fn
        self._button_index = button_index
        self._save_fn = save_fn

        self._defn = ButtonDef()
        self._defn.label = label
        self._defn.color_index = _color_index(color)
        self._defn.bg_color = bg
        self._defn.bold = bold

        # tkinter sizes buttons in text units, not pixels -- approximate
        # the Qt min_w/min_h (pixels) as character/line counts so the
        # relative proportions (wide function keys vs. square digit keys)
        # still read correctly.
        self._char_w = max(2, min_w // 9)
        self._char_h = max(1, min_h // 20)

        super().__init__(parent, **kwargs)
        self.configure(command=self._execute)
        self.bind("<Button-3>", self._open_editor)  # right-click
        self._apply_defn()

    # -- appearance -----------------------------------------------------------

    def _apply_defn(self):
        d = self._defn
        weight = "bold" if d.bold else "normal"
        self.configure(
            text=d.label, fg=d.color, bg=d.bg_color,
            activebackground="#c0bdb5", activeforeground=d.color,
            font=("Arial", 10, weight),
            relief="raised", bd=2,
            width=self._char_w, height=self._char_h,
        )

    def apply_button_def(self, defn: ButtonDef):
        """Apply an externally-loaded ButtonDef (e.g. from defbuttons.ini)."""
        defn.bg_color = self._defn.bg_color
        defn.bold = self._defn.bold
        self._defn = defn
        self._apply_defn()

    # -- action ---------------------------------------------------------------

    def _execute(self):
        if self._cpu is None:
            return
        # Send the button's Code= value exactly as stored in defbuttons.ini,
        # with no translation -- same fix as beboputer_v7.tools.diy_button
        # (this session's DIYButton._execute() bug fix): the old ASCII-hex
        # translation silently corrupted any non-digit button whose code
        # happened to land in $30-$39/$41-$46 (Cos $39->$09, Tan $38->$08).
        self._cpu._write(_FIXED_PORT, self._defn.value)

    # -- editor ---------------------------------------------------------------

    def _open_editor(self, event=None):
        """Open Configure Button Attributes (only when the calculator is off)."""
        if self._powered_fn is not None and self._powered_fn():
            return

        def _on_apply(new_defn):
            self._defn = new_defn
            self._apply_defn()
            if self._save_fn is not None:
                self._save_fn(self._button_index, self._defn)

        ConfigureButtonAttributes(self.winfo_toplevel(), self._defn, _on_apply)
