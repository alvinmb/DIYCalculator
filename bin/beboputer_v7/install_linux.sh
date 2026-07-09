#!/usr/bin/env bash
# ================================================================
# install_linux.sh — Beboputer installer for Linux / Raspberry Pi
#
# Usage:
#   chmod +x install_linux.sh
#   ./install_linux.sh
#
# What it does:
#   1. Installs Python 3 and PyQt5 if not already present
#   2. Copies the app to ~/.local/share/beboputer
#   3. Creates a launcher script at ~/.local/bin/beboputer
#   4. Creates a .desktop file for the application menu
# ================================================================

set -e

APP_NAME="Beboputer"
INSTALL_DIR="$HOME/.local/share/beboputer"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
SCRIPT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"   # project root

echo "==> Installing $APP_NAME..."
echo "    Source : $SCRIPT_DIR"
echo "    Target : $INSTALL_DIR"

# ── 1. Check Python 3 ─────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "==> Installing Python 3..."
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip
fi

PYTHON=$(command -v python3)
echo "    Python : $PYTHON ($(python3 --version))"

# ── 2. Install PyQt5 ──────────────────────────────────────────────
echo "==> Checking PyQt5..."
if ! python3 -c "from PyQt5.QtWidgets import QApplication" 2>/dev/null; then
    echo "==> Installing PyQt5..."
    # Try apt first (faster on Pi, avoids building from source)
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y python3-pyqt5
    else
        pip3 install pyqt5 --break-system-packages
    fi
fi
echo "    PyQt5  : OK"

# ── 3. Copy application files ─────────────────────────────────────
echo "==> Copying application files..."
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

cp -r "$SCRIPT_DIR/bin"             "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/BITMAPS"         "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/Config"          "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/Data"            "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/databook"        "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/WorkInProgress"  "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/tutorial"        "$INSTALL_DIR/"

# Stale bytecode caches bloat the copy and can shadow the .py sources
# with a different Python version on the target machine.
find "$INSTALL_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "    Files copied to $INSTALL_DIR"

# ── 4. Create launcher script ─────────────────────────────────────
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/beboputer" << EOF
#!/usr/bin/env bash
# Beboputer launcher
cd "$INSTALL_DIR"
exec python3 "$INSTALL_DIR/bin/run_beboputer_v7.py" "\$@"
EOF

chmod +x "$BIN_DIR/beboputer"
echo "    Launcher: $BIN_DIR/beboputer"

# ── 5. Create .desktop entry (application menu) ───────────────────
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_DIR/beboputer.desktop" << EOF
[Desktop Entry]
Version=1.0
Name=PY-DIYCALCULATOR
Comment=Beboputer Virtual 8-bit Computer
Exec=$BIN_DIR/beboputer
Icon=$INSTALL_DIR/BITMAPS/beboputer.png
Terminal=false
Type=Application
Categories=Education;Emulator;
Keywords=cpu;assembler;calculator;retro;
EOF

# Update desktop database if available
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

echo "    Desktop entry: $DESKTOP_DIR/beboputer.desktop"

# ── 6. Add ~/.loca