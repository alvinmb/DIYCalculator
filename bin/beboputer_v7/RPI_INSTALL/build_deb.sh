#!/usr/bin/env bash
# ================================================================
# build_deb.sh — Build beboputer_<version>_all.deb for Raspberry Pi
#
# CAN BE RUN ON WINDOWS via WSL:
#   wsl bash bin/beboputer_v7/RPI_INSTALL/build_deb.sh
#
# Or run directly on Linux / Raspberry Pi:
#   bash bin/beboputer_v7/RPI_INSTALL/build_deb.sh
#
# Output: dist/beboputer_<version>_all.deb
#
# To install on Pi:
#   sudo dpkg -i beboputer_<version>_all.deb
#   sudo apt-get install -f     # fix any missing dependencies
# ================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

PKG_NAME="beboputer"
# Version is the single source of truth in bin/beboputer_v7/__init__.py
# (__version__) — nothing to edit here, this always tracks the app.
PKG_VERSION="$(cd "$PROJECT_ROOT/bin" && python3 -c "from beboputer_v7 import __version__; print(__version__)")"
if [ -z "$PKG_VERSION" ]; then
    echo "ERROR: Could not read __version__ from beboputer_v7 (is python3 available?)."
    exit 1
fi
PKG_ARCH="all"           # Python source — runs on Pi 1/2/3/4/5, any ARM
INSTALL_ROOT="/usr"

# Stage and build in /tmp (native Linux FS) so dpkg-deb can set
# proper Unix permissions — Windows-mounted paths (/mnt/c/...) don't
# support them and cause dpkg-deb to fail.
STAGING="/tmp/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}"
DEB_TMP="/tmp/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"
DEB_OUT="$PROJECT_ROOT/dist/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"

echo "============================================================"
echo " Beboputer Raspberry Pi .deb Builder"
echo " Version      : $PKG_VERSION"
echo " Project root : $PROJECT_ROOT"
echo " Output       : $DEB_OUT"
echo "============================================================"

# ── Check dpkg-deb is available ──────────────────────────────────
if ! command -v dpkg-deb &>/dev/null; then
    echo "ERROR: dpkg-deb not found."
    echo "  On WSL/Ubuntu:  sudo apt-get install dpkg"
    exit 1
fi

# ── Clean old staging area ────────────────────────────────────────
rm -rf "$STAGING"

# ── Create directory layout ───────────────────────────────────────
APP_DIR="$STAGING/$INSTALL_ROOT/share/$PKG_NAME"
BIN_DIR="$STAGING/$INSTALL_ROOT/bin"
DESKTOP_DIR="$STAGING/$INSTALL_ROOT/share/applications"
DEBIAN_DIR="$STAGING/DEBIAN"

mkdir -p "$APP_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$DEBIAN_DIR"

# ── Copy application files ────────────────────────────────────────
# paths.py resolves project root as 2 levels above its own directory:
#   dirname(paths.py) = /usr/share/beboputer/bin/beboputer_v7
#   ../..             = /usr/share/beboputer        ← APP_DIR
#
# So BITMAPS/, Config/, Data/, help/, etc. must sit directly inside APP_DIR
# (/usr/share/beboputer/), NOT inside bin/.
# bin/ holds the Python source and sits one level deeper.
echo "==> Copying application files..."
cp -r "$PROJECT_ROOT/bin"             "$APP_DIR/"
cp -r "$PROJECT_ROOT/BITMAPS"         "$APP_DIR/"
cp -r "$PROJECT_ROOT/Config"          "$APP_DIR/"
cp -r "$PROJECT_ROOT/Data"            "$APP_DIR/"
cp -r "$PROJECT_ROOT/WorkInProgress"  "$APP_DIR/"
cp -r "$PROJECT_ROOT/tutorial"        "$APP_DIR/"
cp -r "$PROJECT_ROOT/help"            "$APP_DIR/"

# The original Data Book PDF is superseded by help/databook/ (an HTML
# conversion) and is no longer shipped. It may still be sitting in Data/
# in the repo (left there rather than deleted), so strip it from the
# staged copy here -- this runs in /tmp (native Linux FS), so no
# permission issues even if the source-tree copy itself couldn't be removed.
rm -f "$APP_DIR/Data/The Official DIY Calculator Data Book.pdf"

# help/databook/ was regenerated as flat page images (page-NNN.png); the
# old databookNNN.png files (previous pdftohtml conversion attempt) may
# still be sitting alongside them in the repo, so strip those too.
rm -f "$APP_DIR"/help/databook/databook[0-9][0-9][0-9].png

# Strip stale bytecode caches -- they bloat the package and can shadow
# the .py sources with a different Python version on the target machine.
# Glob also catches "__pycache___bak_*"-style backup dirs some editing
# tools leave behind, not just the exact "__pycache__" name.
find "$APP_DIR" -type d -name "__pycache__*" -exec rm -rf {} + 2>/dev/null || true

# ── Launcher script ───────────────────────────────────────────────
cat > "$BIN_DIR/beboputer" << 'EOF'
#!/usr/bin/env bash
exec python3 /usr/share/beboputer/bin/run_beboputer_v7.py "$@"
EOF
chmod 755 "$BIN_DIR/beboputer"

# ── Desktop entry ─────────────────────────────────────────────────
cat > "$DESKTOP_DIR/beboputer.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Name=PY-DIYCALCULATOR
GenericName=Virtual 8-bit Computer
Comment=Beboputer Virtual 8-bit CPU Emulator
Exec=/usr/bin/beboputer
Icon=/usr/share/beboputer/BITMAPS/beboputer.png
Terminal=false
Type=Application
Categories=Education;Emulator;
Keywords=cpu;assembler;calculator;retro;
EOF

# ── DEBIAN/control ────────────────────────────────────────────────
cat > "$DEBIAN_DIR/control" << EOF
Package: $PKG_NAME
Version: $PKG_VERSION
Architecture: $PKG_ARCH
Maintainer: Alvin Brown & Clive Maxfield
Depends: python3 (>= 3.8), python3-pyqt5
Section: education
Priority: optional
Homepage: https://www.clivemaxfield.com/diycalculator/downloads.shtml
Description: PY-DIYCALCULATOR — Beboputer Virtual 8-bit Computer
 A PyQt5 desktop application that emulates a virtual 8-bit CPU
 with calculator panel, workbench I/O, assembler/editor, memory
 walker, and terminal. Designed for learning computer architecture.
EOF

# ── DEBIAN/postinst — run after install ──────────────────────────
cat > "$DEBIAN_DIR/postinst" << 'EOF'
#!/bin/bash
set -e
# Update desktop database so the app appears in menus
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi
echo "Beboputer installed. Run with: beboputer"
EOF
chmod 755 "$DEBIAN_DIR/postinst"

# ── DEBIAN/prerm — run before uninstall ──────────────────────────
cat > "$DEBIAN_DIR/prerm" << 'EOF'
#!/bin/bash
set -e
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi
EOF
chmod 755 "$DEBIAN_DIR/prerm"

# ── Fix permissions ───────────────────────────────────────────────
find "$STAGING" -type d -exec chmod 755 {} \;
find "$STAGING" -type f ! -name "postinst" ! -name "prerm" \
     ! -name "beboputer" -exec chmod 644 {} \;

# ── Build the .deb (in /tmp — proper Linux FS) ───────────────────
echo "==> Building .deb package..."
dpkg-deb --build --root-owner-group "$STAGING" "$DEB_TMP"

# ── Copy .deb to Windows dist folder ─────────────────────────────
mkdir -p "$PROJECT_ROOT/dist"
cp "$DEB_TMP" "$DEB_OUT"

# ── Clean up staging and temp .deb ───────────────────────────────
rm -rf "$STAGING" "$DEB_TMP"

echo ""
echo "============================================================"
echo " Done!"
echo " Package : $DEB_OUT"
echo ""
echo " To install on Raspberry Pi:"
echo "   Copy the .deb to the Pi, then run:"
echo "   sudo dpkg -i beboputer_${PKG_VERSION}_${PKG_ARCH}.deb"
echo "   sudo apt-get install -f"
echo "============================================================"
