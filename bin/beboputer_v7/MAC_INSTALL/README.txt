Beboputer — macOS Installer Build
==================================

FILES
-----
  beboputer_mac.spec   PyInstaller spec (produces Beboputer.app)
  build_mac.sh         One-shot build script (app + DMG)
  README.txt           This file

REQUIREMENTS (one-time setup on the Mac)
-----------------------------------------
  1. Python 3 — comes with macOS or install via https://python.org
  2. PyQt5:
       pip3 install pyqt5
  3. PyInstaller (build_mac.sh installs it automatically if missing)

HOW TO BUILD
------------
  Open Terminal, cd to the project root, then run:

      cd /path/to/Bebop_python
      bash bin/beboputer_v7/MAC_INSTALL/build_mac.sh

  Output:
      dist/Beboputer.app           — the standalone app bundle
      dist/BeboputerInstaller.dmg  — drag-and-drop DMG installer

HOW TO INSTALL (end-user)
--------------------------
  1. Double-click BeboputerInstaller.dmg
  2. Drag Beboputer into the Applications folder shortcut
  3. Eject the DMG
  4. Launch from Applications

OPTIONAL — App icon
--------------------
  Add a beboputer.icns file to this MAC_INSTALL/ folder, then
  uncomment the two 'icon=' lines in beboputer_mac.spec.

OPTIONAL — Code signing
------------------------
  Set codesign_identity in beboputer_mac.spec to your
  Apple Developer ID certificate string, e.g.:
      codesign_identity='Developer ID Application: Your Name (TEAMID)'
