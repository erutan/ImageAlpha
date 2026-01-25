#!/bin/bash
set -euo pipefail

# This script bundles Homebrew libraries required by pngquant into the app bundle
# and fixes the library paths to be relative to the executable.
# Run this BEFORE signing.
#
# Usage: ./bundle-pngquant-libs.sh /path/to/ImageAlpha.app

if [ $# -ne 1 ]; then
    echo "Usage: $0 /path/to/ImageAlpha.app"
    exit 1
fi

APP="$1"
MACOS_DIR="$APP/Contents/MacOS"
PNGQUANT="$MACOS_DIR/pngquant"

if [ ! -f "$PNGQUANT" ]; then
    echo "ERROR: pngquant not found at $PNGQUANT"
    exit 1
fi

echo "=== Bundling pngquant libraries into $APP ==="

# Libraries to bundle (from Homebrew)
LCMS2_SRC="/opt/homebrew/opt/little-cms2/lib/liblcms2.2.dylib"
LIBPNG_SRC="/opt/homebrew/opt/libpng/lib/libpng16.16.dylib"

# Check if libraries exist
if [ ! -f "$LCMS2_SRC" ]; then
    echo "ERROR: liblcms2 not found at $LCMS2_SRC"
    echo "Install with: brew install little-cms2"
    exit 1
fi

if [ ! -f "$LIBPNG_SRC" ]; then
    echo "ERROR: libpng not found at $LIBPNG_SRC"
    echo "Install with: brew install libpng"
    exit 1
fi

# Copy libraries to MacOS directory (same as pngquant)
echo "Copying liblcms2.2.dylib..."
cp "$LCMS2_SRC" "$MACOS_DIR/liblcms2.2.dylib"

echo "Copying libpng16.16.dylib..."
cp "$LIBPNG_SRC" "$MACOS_DIR/libpng16.16.dylib"

# Fix library paths in pngquant to use @executable_path
echo "Fixing library paths in pngquant..."
install_name_tool -change "/opt/homebrew/opt/little-cms2/lib/liblcms2.2.dylib" "@executable_path/liblcms2.2.dylib" "$PNGQUANT"
install_name_tool -change "/opt/homebrew/opt/libpng/lib/libpng16.16.dylib" "@executable_path/libpng16.16.dylib" "$PNGQUANT"

# Fix the library IDs to be relative (for proper signing)
echo "Fixing library IDs..."
install_name_tool -id "@executable_path/liblcms2.2.dylib" "$MACOS_DIR/liblcms2.2.dylib"
install_name_tool -id "@executable_path/libpng16.16.dylib" "$MACOS_DIR/libpng16.16.dylib"

echo ""
echo "=== Verifying ==="
echo "pngquant dependencies:"
otool -L "$PNGQUANT" | grep -E "lcms|libpng"

echo ""
echo "=== Done ==="
echo "Libraries bundled. Now run sign-for-notarization.sh to sign everything."
