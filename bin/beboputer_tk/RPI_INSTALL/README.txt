Beboputer (tkinter build) — Raspberry Pi Installer
====================================================

FILES
-----
  build_deb.sh      Builds beboputer_<version>_all.deb  (run on Windows/WSL or Linux)
  build_deb.bat     Windows wrapper that runs build_deb.sh via WSL
  README.txt        This file

Mirrors bin/beboputer_v7/RPI_INSTALL/ exactly, launching
run_beboputer_tk.py instead of run_beboputer_v7.py and depending on
python3-tk instead of python3-pyqt5. Package name stays "beboputer" --
this is the eventual successor build, not a separate product, so
installing it upgrades an existing Qt-build install of the same
package name in place.

HOW TO BUILD
============

  Build on Windows using WSL (or any Linux machine):

    wsl bash bin/beboputer_tk/RPI_INSTALL/build_deb.sh

  Or directly on Linux / a Raspberry Pi:

    bash bin/beboputer_tk/RPI_INSTALL/build_deb.sh

  This produces:  dist/beboputer_<version>_all.deb
  (<version> comes from bin/beboputer_v7/__init__.py's __version__ --
  beboputer_tk re-exports the same constant, so there's only ever one
  version number for the app regardless of which UI build you package.)

  Copy the .deb to the Raspberry Pi, then on the Pi run:

    sudo dpkg -i beboputer_<version>_all.deb
    sudo apt-get install -f        # installs any missing dependencies

  To uninstall later:

    sudo apt-get remove beboputer

WHAT GETS INSTALLED
====================
  /usr/share/beboputer/    — application files (bin/, BITMAPS/, Config/)
  /usr/bin/beboputer        — launcher (type 'beboputer' anywhere)
  /usr/share/applications/beboputer.desktop — appears in Pi app menu

REQUIREMENTS (handled automatically)
======================================
  python3 (>= 3.8)
  python3-tk

SUPPORTED PI MODELS
====================
  Package architecture is 'all' (Python source, not compiled) so it
  runs on every Pi model: Pi 1, 2, 3, 4, 5, Zero, Zero 2W — any OS
  based on Raspberry Pi OS / Raspbian / Debian.
