#!/usr/bin/env bash
# ================================================================
# build_mac.sh — Build Beboputer.app + BeboputerInstaller.dmg
# (tkinter build)
#
# MUST be run on an actual Mac -- PyInstaller does not cross-compile,
# so this cannot produce a working macOS app from Linux or Windows.
# Mirrors bin/beboputer_v7/MAC_INSTALL/build_mac.sh (the old PyQt5
# build's script) exactly in structure, pointed at the tkinter spec
# instead.
#
# Run from the project root (Bebop_python/):
#   cd /path/to/Bebop_python
#   bash bin/beboputer_tk/MAC_INSTALL/build_mac.sh
#
# What it does:
#   1. Installs PyInstaller if missing
#   2. Removes old dist/Beboputer.app to avoid permission errors
#   3. Runs PyInstaller -> dist/Beboputer.app
#   4. Creates dist/BeboputerInstaller.dmg via hdiutil
#
# Requirements:
#   macOS (tested on 12+), Python 3 with tkinter (python.org's macOS
#   installer bundles it already -- no separate package needed), pip3
# ================================================================

set -e

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "ERROR: this script builds a macOS .app/.dmg and must be run on macOS."
    echo "PyInstaller does not cross-compile -- see the comment at the top of this file."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SPEC="$SCRIPT_DIR/../beboputer_tk.spec"
DIST_DIR="$PROJECT_ROOT/dist"
APP="$DIST_DIR/Beboputer.app"
DMG="$DIST_DIR/BeboputerInstaller.dmg"
VOL_NAME="Beboputer"

echo "============================================================"
echo " Beboputer macOS Build (tkinter)"
echo " Project root : $PROJECT_ROOT"
echo "============================================================"

# ── 1. Check / install PyInstaller ───────────────────────────────
if ! python3 -m PyInstaller --version &>/dev/null; then
    echo "==> Installing PyInstaller..."
    pip3 install pyinstaller
fi

# ── 2. Confirm tkinter is actually importable ────────────────────
if ! python3 -c "import tkinter" &>/dev/null; then
    echo "ERROR: python3 -c 'import tkinter' failed."
    echo "Use the python.org macOS installer (bundles tkinter) rather than a"
    echo "from-source/Homebrew Python built without it."
    exit 1
fi

# ── 3. Remove old .app/.dmg so PyInstaller can write clean ───────
if [ -d "$APP" ]; then
    echo "==> Removing old $APP ..."
    rm -rf "$APP"
fi
if [ -f "$DMG" ]; then
    echo "==> Removing old $DMG ..."
    rm -f "$DMG"
fi

# ── 4. PyInstaller ────────────────────────────────────────────────
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

# ── 5. Create DMG ────────────────────────────────────────────────
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
echo " App       : $APP"
echo " Installer : $DMG"
echo "============================================================"
