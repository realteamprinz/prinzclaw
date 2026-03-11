#!/bin/bash
# Build prinzclaw macOS .app and .dmg
# Usage: ./macos/build.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build"
DIST_DIR="$PROJECT_ROOT/dist"

echo "============================================"
echo "  PRINZCLAW macOS BUILD"
echo "  FORGED WITH PRINZCLAW"
echo "============================================"

# Step 0: Ensure we're in project root
cd "$PROJECT_ROOT"

# Step 1: Check/install dependencies
echo ""
echo "[1/5] Checking dependencies..."

if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "  Installing PyInstaller..."
    pip3 install pyinstaller
fi

if ! python3 -c "import rumps" 2>/dev/null; then
    echo "  Installing rumps..."
    pip3 install rumps
fi

# Install all project deps
pip3 install -q aiohttp pyyaml httpx

# Step 2: Generate icons
echo "[2/5] Generating icons..."
python3 macos/create_icon.py

# Step 3: Build .app with PyInstaller
echo "[3/5] Building macOS .app..."
pyinstaller \
    --noconfirm \
    --clean \
    --distpath "$DIST_DIR" \
    --workpath "$BUILD_DIR" \
    macos/prinzclaw.spec

echo "  .app built at: $DIST_DIR/prinzclaw.app"

# Step 4: Create DMG
echo "[4/5] Creating DMG installer..."

DMG_NAME="prinzclaw-1.0.0-macOS"
DMG_DIR="$BUILD_DIR/dmg"
DMG_PATH="$DIST_DIR/$DMG_NAME.dmg"

rm -rf "$DMG_DIR"
mkdir -p "$DMG_DIR"
cp -R "$DIST_DIR/prinzclaw.app" "$DMG_DIR/"
ln -s /Applications "$DMG_DIR/Applications"

# Check if create-dmg is available
if command -v create-dmg &>/dev/null; then
    create-dmg \
        --volname "prinzclaw" \
        --volicon "macos/resources/app_icon.png" \
        --background "macos/resources/dmg_background.png" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 80 \
        --icon "prinzclaw.app" 160 200 \
        --icon "Applications" 440 200 \
        --hide-extension "prinzclaw.app" \
        --app-drop-link 440 200 \
        --no-internet-enable \
        "$DMG_PATH" \
        "$DMG_DIR"
else
    echo "  create-dmg not found, using hdiutil..."
    rm -f "$DMG_PATH"
    hdiutil create \
        -volname "prinzclaw" \
        -srcfolder "$DMG_DIR" \
        -ov -format UDZO \
        "$DMG_PATH"
fi

echo "  DMG created at: $DMG_PATH"

# Step 5: Summary
echo ""
echo "============================================"
echo "  BUILD COMPLETE"
echo "============================================"
echo "  .app: $DIST_DIR/prinzclaw.app"
echo "  .dmg: $DMG_PATH"
echo ""

APP_SIZE=$(du -sh "$DIST_DIR/prinzclaw.app" 2>/dev/null | cut -f1)
DMG_SIZE=$(du -sh "$DMG_PATH" 2>/dev/null | cut -f1)
echo "  App size: $APP_SIZE"
echo "  DMG size: $DMG_SIZE"
echo ""
echo "  FORGED WITH PRINZCLAW"
echo "============================================"
