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

"""Application entry point — boots Qt and shows the main window."""

import sys
import os

from PyQt5.QtWidgets import QApplication, QSplashScreen, QToolTip
from PyQt5.QtGui import QPixmap, QPalette, QColor
from PyQt5.QtCore import Qt, QTimer

from pathlib import Path

from .main_window import BebopMain
from .styles import STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setStyle("Windows")
    app.setStyleSheet(STYLESHEET)

    # Tooltip colors: neither the QSS "QToolTip {}" rule in styles.py nor
    # QApplication.setPalette() reliably wins here -- a button that sets
    # its own QSS background-color/color (e.g. the plain command buttons'
    # default grey #d4d0c8, or Memory Walker's red "RUN to BP" text) can
    # still leak that into its OWN tooltip, because Qt's "Windows" style
    # resolves each widget's tooltip from that widget's own polished
    # palette rather than always falling back to the app-wide one.
    # QToolTip.setPalette() is the dedicated, most-specific API Qt
    # provides for tooltip colors and takes priority over that per-widget
    # leak, so it's the one that actually sticks everywhere.
    _pal = app.palette()
    _pal.setColor(QPalette.ToolTipBase, QColor("#ffffcc"))
    _pal.setColor(QPalette.ToolTipText, QColor("#000000"))
    app.setPalette(_pal)
    QToolTip.setPalette(_pal)
    app.setStyleSheet(
        app.styleSheet()
        + "\nQToolTip { background-color: #ffffcc; color: #000000; "
          "border: 1px solid #808080; padding: 2px 4px; }"
    )

    # --- Splash screen -------------------------------------------------------
    # splash.png lives in the same directory as run_beboputer_v7.py (bin/ on
    # both Windows source and Pi .deb install).  Using __file__ avoids the
    # resource_path('bin', ...) double-bin problem on Debian.
    splash_path = str(Path(__file__).resolve().parent.parent / 'splash.png')
    splash = None
    if os.path.exists(splash_path):
        pix = QPixmap(splash_path)
        if not pix.isNull():
            # Scale to a reasonable splash size (max 480 wide) keeping aspect
            if pix.width() > 480:
                pix = pix.scaledToWidth(480, Qt.SmoothTransformation)
            splash = QSplashScreen(pix, Qt.WindowStaysOnTopHint)
            splash.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint)
            splash.show()
            app.processEvents()
    # -------------------------------------------------------------------------

    window = BebopMain()

    if splash:
        # Close splash and show main window after 2.5 seconds
        QTimer.singleShot(2500, lambda: (splash.finish(window), window.show()))
    else:
        window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
