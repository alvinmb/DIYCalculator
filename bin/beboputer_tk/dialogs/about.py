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

import os
import tkinter as tk
from tkinter import messagebox

try:
    from beboputer_v7 import __version__
except ImportError:  # pragma: no cover
    __version__ = "0.0.0-dev"

try:
    from beboputer_v7.styles import C
except ImportError:  # pragma: no cover
    C = {"blue": "#000080", "green_mid": "#004d00"}

try:
    from beboputer_v7.paths import resource_path as _resource_path
except ImportError:  # pragma: no cover
    def _resource_path(*parts: str) -> str:
        return os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", *parts)
        )

# HTML conversion of "The Official DIY Calculator Data Book.pdf" (pdftohtml,
# one background PNG per page + an absolute-positioned text overlay so the
# original schematics/pinout diagrams render exactly as in the PDF). Lives
# under help/ alongside beboputer_v7_help.html (see beboputer_tk.spec's
# datas list -- the whole help/ directory is shipped, so this travels with
# it automatically in both the source checkout and the frozen/packaged
# build). The original PDF is no longer bundled in any install.
_DATA_BOOK_HTML = ("help", "databook", "index.html")


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

        # Splash image removed (2026-08-02) -- title/version now sit alone
        # at the top instead of beside it.
        tk.Label(
            root, text="PY-DIYCALCULATOR", fg=C["blue"], bg="#c0c0c0",
            font=("Arial", 20, "bold"), justify="left", anchor="w",
        ).pack(fill="x", pady=(0, 6))

        tk.Label(
            root, text=f"tkinter Edition  —  v{__version__}",
            fg=C["green_mid"], bg="#c0c0c0", font=("Arial", 15),
            justify="left", anchor="w",
        ).pack(fill="x")

        tk.Label(
            root,
            text=(
                'Based on the Beboputer virtual 8-bit CPU from\n'
                '"How Computers Do Math"\n'
                'by Clive "Max" Maxfield & Alvin Brown\n\n'
                'Rewritten in Python 3 + tkinter.'
            ),
            fg=C["green_mid"], bg="#c0c0c0", font=("Arial", 16), justify="center",
        ).pack(pady=(16, 16))

        btn_row = tk.Frame(root, bg="#c0c0c0")
        btn_row.pack(pady=(0, 0))

        tk.Button(
            btn_row, text="Beboputer Databook", font=("Arial", 13, "bold"),
            command=self._open_data_book,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            btn_row, text="Dismiss", font=("Arial", 13, "bold"),
            command=self.destroy,
        ).pack(side="left")

    def _open_data_book(self):
        """Open the HTML edition of the DIY Calculator Data Book in the
        system's default browser. Same source/bundle path logic as
        main_window._show_help()."""
        import webbrowser
        path = _resource_path(*_DATA_BOOK_HTML)
        if os.path.exists(path):
            webbrowser.open(f"file:///{path.replace(os.sep, '/')}")
        else:
            messagebox.showinfo("Beboputer Databook", f"Databook not found:\n{path}")
