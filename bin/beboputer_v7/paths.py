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
paths.py — portable data-file resolver.

Works in two modes:

1. **Source / development**
   ``resource_path('BITMAPS', 'USEG0.BMP')`` resolves relative to the
   project root (the folder that *contains* ``bin/``).  This is two
   directory levels above this file::

       <project_root>/
           BITMAPS/
           Config/
           bin/
               beboputer_v7/
                   paths.py   ← this file

2. **PyInstaller bundle** (``sys.frozen == True``)
   All data files are extracted to ``sys._MEIPASS`` by the bundler.
   ``resource_path`` simply joins the requested parts onto that temp root.

Usage
-----
    from .paths import resource_path

    bmp  = resource_path('BITMAPS', 'USEG0.BMP')
    ini  = resource_path('Config', 'DIYCALC.INI')
    html = resource_path('beboputer_v7_help.html')
"""

import os
import sys


def resource_path(*parts: str) -> str:
    """Return the absolute path to a bundled data file or folder.

    Parameters
    ----------
    *parts:
        Path components relative to the project / bundle root,
        e.g. ``resource_path('BITMAPS', 'USEG0.BMP')``.
    """
    if getattr(sys, 'frozen', False):
        # Running inside a PyInstaller bundle — data lives in _MEIPASS.
        base = sys._MEIPASS                          # type: ignore[attr-defined]
    else:
        # Running from source — project root is two levels above this file:
        # paths.py → beboputer_v7/ → bin/ → <project_root>/
        base = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
        )
    return os.path.normpath(os.path.join(base, *parts))
