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

"""About dialog -- tkinter port of beboputer_v7/dialogs/about.py."""

from __future__ import annotations

import tkinter as tk

try:
    from beboputer_v7 import __version__
except ImportError:  # pragma: no cover
    __version__ = "0.0.0-dev"

try:
    from beboputer_v7.styles import C
except ImportError:  # pragma: no cover
    C = {"blue": "#000080", "green_mid": "#004d00"}


class AboutDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("About PY-DIYCALCULATOR")
        self.resizable(False, False)
        self.configure(bg="#c0c0c0")
        self._build()
        self.transient(parent)
        self.grab_set()

    def _build(self):
        root = tk.Frame(self, bg="#c0c0c0", padx=24, pady=20)
        root.pack(fill="both", expand=True)

        tk.Label(
            root, text="PY-DIYCALCULATOR", fg=C["blue"], bg="#c0c0c0",
            font=("Arial", 17, "bold"),
        ).pack(pady=(0, 6))

        tk.Label(
            root, text=f"tkinter Edition  —  v{__version__}",
            fg=C["green_mid"], bg="#c0c0c0", font=("Arial", 12),
        ).pack(pady=(0, 12))

        tk.Label(
            root,
            text=(
                'Based on the Beboputer virtual 8-bit CPU from\n'
                '"How Computers Do Math"\n'
                'by Clive "Max" Maxfield & Alvin Brown\n\n'
                'Rewritten in Python 3 + tkinter.'
            ),
            fg=C["green_mid"], bg="#c0c0c0", font=("Arial", 13), justify="center",
        ).pack(pady=(0, 16))

        tk.Button(
            root, text="Dismiss", font=("Arial", 10, "bold"),
            command=self.destroy,
        ).pack()
