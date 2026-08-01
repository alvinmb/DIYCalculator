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

"""System Clock dialog -- set the simulated CPU clock speed. tkinter
port of beboputer_v7/dialogs/system_clock.py.

Qt's QDialog.exec_() (blocks the caller, returns Accepted/Rejected)
has no exact tkinter equivalent widget, but the standard tkinter
pattern -- grab_set() + wait_window() -- reproduces the same blocking-
modal behaviour: ask_hz() below blocks the caller exactly like Qt's
exec_() did, and returns the validated int (or None if cancelled),
replacing the Qt version's two-step "exec_() then .value()" with one
call.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

try:
    from beboputer_v7.styles import C
except ImportError:  # pragma: no cover
    C = {"lcd_bg": "#c8f0c8", "btn_bdr": "#888888"}


class SystemClockDialog(tk.Toplevel):
    def __init__(self, parent, current_hz):
        super().__init__(parent)
        self.title("System Clock")
        self.resizable(False, False)
        self.configure(bg="#c0c0c0")
        self._hz = current_hz
        self.result = None  # set on OK; stays None on Cancel
        self._build()
        self.transient(parent)
        self.grab_set()

    def _build(self):
        root = tk.Frame(self, bg="#c0c0c0", padx=16, pady=16)
        root.pack(fill="both", expand=True)

        # Label/entry fonts matched to CPU Registers panel: Arial 14
        # bold for descriptive labels, Courier New 18 bold for the
        # LCD-style numeric readout/entry (see cpu_panel.py).
        form = tk.Frame(root, bg="#c0c0c0")
        form.pack(fill="x")
        tk.Label(form, text="Clock Speed (Hz):", bg="#c0c0c0",
                 font=("Arial", 14, "bold")).pack(side="left")
        self._hz_var = tk.StringVar(value=str(self._hz))
        entry = tk.Entry(
            form, textvariable=self._hz_var, justify="right", width=10,
            bg=C["lcd_bg"], fg="#000000", relief="sunken", bd=2,
            font=("Courier New", 18, "bold"),
        )
        entry.pack(side="left", padx=(8, 0))
        entry.bind("<Return>", lambda e: self._apply())
        entry.focus_set()
        entry.select_range(0, "end")

        tk.Label(root, text="Range: 1 - 10 000 Hz", bg="#c0c0c0",
                 font=("Arial", 14, "bold")).pack(anchor="e", pady=(8, 0))

        # Bigger buttons: larger font plus real padding (was text-hugging
        # with no padx/pady at all), same BTN_PADX/BTN_PADY convention
        # used for Memory Walker's buttons.
        BTN_FONT = ("Arial", 14, "bold")
        BTN_PADX, BTN_PADY = 14, 8
        btn_row = tk.Frame(root, bg="#c0c0c0")
        btn_row.pack(fill="x", pady=(14, 0))
        tk.Button(btn_row, text="Cancel", font=BTN_FONT,
                  padx=BTN_PADX, pady=BTN_PADY,
                  command=self._cancel).pack(side="right", padx=(6, 0))
        tk.Button(btn_row, text="OK", font=BTN_FONT,
                  padx=BTN_PADX, pady=BTN_PADY,
                  command=self._apply, default="active").pack(side="right")

    def _apply(self):
        try:
            val = int(self._hz_var.get().strip())
            if not (1 <= val <= 10000):
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Invalid Value",
                "Please enter a whole number between 1 and 10 000.",
                parent=self,
            )
            return
        self.result = val
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


def ask_hz(parent, current_hz) -> int | None:
    """Show the System Clock dialog modally; return the new Hz value,
    or None if the user cancelled."""
    dlg = SystemClockDialog(parent, current_hz)
    parent.wait_window(dlg)
    return dlg.result
