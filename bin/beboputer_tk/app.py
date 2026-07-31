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

"""Application entry point -- boots tkinter and shows the main window.

tkinter counterpart of beboputer_v7/app.py. DPI awareness must be set
before Tk() is constructed -- see dpi.py for why and what it replaces
from the Qt build.
"""

import os

from . import dpi
from .main_window import BebopMain


def main():
    # Must happen before Tk() -- see dpi.py's module docstring.
    dpi.set_process_dpi_aware()

    import tkinter as tk

    root = tk.Tk()
    dpi.apply_dpi_scaling(root)

    # -- splash screen ---------------------------------------------------
    # Reuses the same splash.png the Qt build uses (bin/splash.png) --
    # plain image asset, no Qt dependency to reuse it.
    splash = None
    try:
        from pathlib import Path
        splash_path = Path(__file__).resolve().parent.parent / "splash.png"
        if splash_path.exists():
            img = tk.PhotoImage(file=str(splash_path))
            # tk.PhotoImage only decodes GIF/PGM/PPM/PNG (PNG needs Tk 8.6+,
            # which every currently-supported Python ships) -- if splash.png
            # is some other format this raises and we just skip the splash.
            splash = tk.Toplevel(root)
            splash.overrideredirect(True)
            w, h = img.width(), img.height()
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            splash.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//2}")
            tk.Label(splash, image=img, bd=0).pack()
            splash.image = img  # keep a reference -- PhotoImage needs one
            splash.attributes("-topmost", True)
            root.withdraw()
            root.update()
    except Exception:
        splash = None

    window = BebopMain(root)

    if splash is not None:
        def _show_main():
            splash.destroy()
            root.deiconify()
        root.after(2500, _show_main)
    else:
        root.deiconify()

    root.mainloop()


if __name__ == "__main__":
    main()
