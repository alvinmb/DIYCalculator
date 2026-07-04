#!/usr/bin/env bash
# ================================================================
# build_mac.sh — Build Beboputer.app + BeboputerInstaller.dmg
#
# Run from the project root (Bebop_python/):
#   cd /path/to/Bebop_python
#   bash bin/beboputer_v7/MAC_INSTALL/build_mac.sh
#
# What it does:
#   1. Installs PyInstaller if missing
#   2. Removes old dist/Beboputer.app to avoid permission errors
#   3. Runs PyInstaller → dist/Beboputer.app
#   4. Creates dist/BeboputerInstaller.dmg via hdiutil
#
# Requirements:
#   macOS (tested on 12+), Python 3, pip3, PyQt5
# ================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SPEC="$SCRIPT_DIR/beboputer_mac.spec"
DIST_DIR="$PROJECT_ROOT/dist"
APP="$DIST_DIR/Beboputer.app"
DMG="$DIST_DIR/BeboputerInstaller.dmg"
VOL_NAME="Beboputer"

echo "============================================================"
echo " Beboputer macOS Build"
echo " Project root : $PROJECT_ROOT"
echo "============================================================"

# ── 1. Check / install PyInstaller ───────────────────────────────
if ! python3 -m PyInstaller --version &>/dev/null; then
    echo "==> Installing PyInstaller..."
    pip3 install pyinstaller --break-system-packages
fi

# ── 2. Remove old .app so PyInstaller can write clean ────────────
if [ -d "$APP" ]; then
    echo "==> Removing old $APP ..."
    rm -rf "$APP"
fi
if [ -f "$DMG" ]; then
    echo "==> Removing old $DMG ..."
    rm -f "$DMG"
fi

# ── 3. PyInstaller ───────────────────────────────────────────────
echo ""
echo "============================================================"
echo " Step 1: PyInstaller — building Beboputer.app"
echo "============================================================"
cd "$PROJECT_ROOT"
python3 -m PyInstaller "$SPEC" --noconfirm

if [ ! -d "$APP" ]; then
    echo ""
    echo "ERROR: PyInstaller finished but $APP was not created."
    exit 1
fi
echo "==> .app created: $APP"

# ── 4. Create DMG ────────────────────────────────────────────────
echo ""
echo "============================================================"
echo " Step 2: hdiutil — creating BeboputerInstaller.dmg"
echo "============================================================"

# Staging folder for DMG contents
STAGING="$DIST_DIR/_dmg_stage"
rm -rf "$STAGING"
mkdir -p "$STAGING"

# Copy .app into staging
cp -r "$APP" "$STAGING/"

# Symlink to /Applications so the user can drag-and-drop
ln -s /Applications "$STAGING/Applications"

# Build the DMG
hdiutil create \
    -volname  "$VOL_NAME" \
    -srcfolder "$STAGING" \
    -ov \
    -format   UDZO \
    "$DMG"

rm -rf "$STAGING"

echo ""
echo "============================================================"
echo " Done!"
echo " Installer : $DMG"
echo "============================================================"
