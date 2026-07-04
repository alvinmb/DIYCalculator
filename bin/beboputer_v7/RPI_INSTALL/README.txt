Beboputer — Raspberry Pi Installer
====================================

FILES
-----
  build_deb.sh      Builds beboputer_7.0.0_all.deb  (run on Windows/WSL or Linux)
  install_rpi.sh    One-shot installer (run directly on the Pi)
  README.txt        This file

TWO WAYS TO INSTALL
====================

── OPTION A: .deb package (recommended) ──────────────────────────

  Build on Windows using WSL (or any Linux machine):

    wsl bash bin/beboputer_v7/RPI_INSTALL/build_deb.sh

  This produces:  dist/beboputer_7.0.0_all.deb

  Copy the .deb to the Raspberry Pi, then on the Pi run:

    sudo dpkg -i beboputer_7.0.0_all.deb
    sudo apt-get install -f        # installs any missing dependencies

  To uninstall later:

    sudo apt-get remove beboputer

── OPTION B: Direct install script ───────────────────────────────

  Copy the whole Bebop_python project folder to the Pi, then run:

    sudo bash bin/beboputer_v7/RPI_INSTALL/install_rpi.sh

  This installs in one step with no build required.

WHAT GETS INSTALLED
====================
  /usr/share/beboputer/   — application files (bin/, BITMAPS/, Config/)
  /usr/local/bin/beboputer — launcher (type 'beboputer' anywhere)
  /usr/share/applications/beboputer.desktop — appears in Pi app menu

REQUIREMENTS (handled automatically)
======================================
  python3 (>= 3.8)
  python3-pyqt5

SUPPORTED PI MODELS
====================
  Package architecture is 'all' (Python source, not compiled) so it
  runs on every Pi model: Pi 1, 2, 3, 4, 5, Zero, Zero 2W — any OS
  based on Raspberry Pi OS / Raspbian / Debian.
