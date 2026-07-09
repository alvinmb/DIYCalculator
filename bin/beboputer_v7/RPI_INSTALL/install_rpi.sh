#!/usr/bin/env bash
# ================================================================
# install_rpi.sh — One-shot installer for Raspberry Pi
#
# Run directly on the Pi from the project root:
#   bash bin/beboputer_v7/RPI_INSTALL/install_rpi.sh
#
# No build step required — installs from Python source.
# ================================================================

set -e

APP_NAME="PY-DIYCALCULATOR"
PKG_NAME="beboputer"
INSTALL_DIR="/usr/share/$PKG_NAME"
BIN_LINK="/usr/local/bin/beboputer"
DESKTOP_DIR="/usr/share/applications"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "============================================================"
echo " $APP_NAME — Raspberry Pi Installer"
echo " Source : $PROJECT_ROOT"
echo " Target : $INSTALL_DIR"
echo "============================================================"

# ── Check running as root ────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo:"
    echo "  sudo bash bin/beboputer_v7/RPI_INSTALL/install_rpi.sh"
    exit 1
fi

# ── 1. Check Python 3 ────────────────────────────────────────────
echo "==> Checking Python 3..."
if ! command -v python3 &>/dev/null; then
    apt-get update -y
    apt-get install -y python3 python3-pip
fi
echo "    $(python3 --version)"

# ── 2. Check PyQt5 ───────────────────────────────────────────────
echo "==> Checking PyQt5..."
if ! python3 -c "from PyQt5.QtWidgets import QApplication" 2>/dev/null; then
    echo "    Installing python3-pyqt5..."
    apt-get install -y python3-pyqt5
fi
echo "    PyQt5 OK"

# ── 3. Install application files ─────────────────────────────────
echo "==> Installing application files to $INSTALL_DIR ..."
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

cp -r "$PROJECT_ROOT/bin"             "$INSTALL_DIR/"
cp -r "$PROJECT_ROOT/BITMAPS"         "$INSTALL_DIR/"
cp -r "$PROJECT_ROOT/Config"          "$INSTALL_DIR/"
cp -r "$PROJECT_ROOT/Data"            "$INSTALL_DIR/"
cp -r "$PROJECT_ROOT/databook"        "$INSTALL_DIR/"
cp -r "$PROJECT_ROOT/WorkInProgress"  "$INSTALL_DIR/"
cp -r "$PROJECT_ROOT/tutorial"        "$INSTALL_DIR/"

# ── 4. Launcher ──────────────────────────────────────────────────
echo "==> Creating launcher at $BIN_LINK ..."
cat > "$BIN_LINK" << EOF
#!/usr/bin/env bash
exec python3 $INSTALL_DIR/bin/run_beboputer_v7.py "\$@"
EOF
chmod 755 "$BIN_LINK"

# ── 5. Desktop entry ─────────────────────────────────────────────
echo "==> Creating desktop entry..."
cat > "$DESKTOP_DIR/beboputer.desktop" << EOF
[Desktop Entry]
Version=1.0
Name=PY-DIYCALCULATOR
GenericName=Virtual 8-bit Computer
Comment=Beboputer Virtual 8-bit CPU Emulator
Exec=$BIN_LINK
Icon=$INSTALL_DIR/BITMAPS/beboputer.png
Terminal=false
Type=Application
Categories=Education;Emulator;
Keywords=cpu;assembler;calculator;retro;
EOF

if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

echo ""
echo "============================================================"
echo " Installation complete!"
echo " Run with:  beboputer"
echo " Or find '$APP_NAME' in the application menu."
echo "========