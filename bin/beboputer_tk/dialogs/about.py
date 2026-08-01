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

try:
    from beboputer_v7 import __version__
except ImportError:  # pragma: no cover
    __version__ = "0.0.0-dev"

try:
    from beboputer_v7.styles import C
except ImportError:  # pragma: no cover
    C = {"blue": "#000080", "green_mid": "#004d00"}

# splash_about.png is a pre-scaled (200x200, dev-time PIL conversion --
# same reasoning as workbench.py's pre-converted BITMAPS PNGs: no
# runtime Pillow dependency, tk.PhotoImage loads PNG natively) copy of
# bin/splash.png (the Qt build's QSplashScreen image, 570x394 native).
# Lives directly in bin/ next to splash.png, NOT under BITMAPS/ or
# resolved via paths.resource_path() -- resource_path()'s project-root
# base would look one directory too high (splash.png/splash_about.png
# sit in bin/ itself, matching Qt app.py's own
# `Path(__file__).resolve().parent.parent / 'splash.png'` lookup from
# bin/beboputer_v7/app.py), so the path here is computed the same way,
# just from dialogs/about.py's own location (bin/beboputer_tk/dialogs/
# -> up two levels -> bin/).
_SPLASH_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "splash_about.png",
))


class AboutDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("About PY-DIYCALCULATOR")
        self.resizable(False, False)
        self.configure(bg="#c0c0c0")
        self._splash_img = None  # kept alive -- PhotoImage is GC'd otherwise
        self._build()
        self.transient(parent)
        self.grab_set()

    def _build(self):
        root = tk.Frame(self, bg="#c0c0c0", padx=24, pady=20)
        root.pack(fill="both", expand=True)

        # Top row: splash image top-left, title/version stacked beside it.
        top = tk.Frame(root, bg="#c0c0c0")
        top.pack(fill="x", anchor="w")

        try:
            self._splash_img = tk.PhotoImage(file=_SPLASH_PATH)
        except tk.TclError:
            self._splash_img = None
        if self._splash_img is not None:
            tk.Label(top, image=self._splash_img, bg="#c0c0c0").pack(
                side="left", anchor="nw", padx=(0, 16)
            )

        text_col = tk.Frame(top, bg="#c0c0c0")
        text_col.pack(side="left", anchor="w", fill="both", expand=True)

        tk.Label(
            text_col, text="PY-DIYCALCULATOR", fg=C["blue"], bg="#c0c0c0",
            font=("Arial", 20, "bold"), justify="left", anchor="w",
        ).pack(fill="x", pady=(0, 6))

        tk.Label(
            text_col, text=f"tkinter Edition  —  v{__version__}",
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

        tk.Button(
            root, text="Dismiss", font=("Arial", 13, "bold"),
            command=self.destroy,
        ).pack()
