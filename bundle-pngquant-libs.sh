#!/bin/bash
set -euo pipefail

# This script bundles universal Homebrew libraries required by pngquant into the app bundle
# and fixes the library paths to be relative to the executable.
# Run this BEFORE signing.
#
# Requires both arm64 (/opt/homebrew) and x86_64 (/usr/local) Homebrew installations
# with libpng and little-cms2 installed.
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

echo "=== Bundling universal pngquant libraries into $APP ==="

# Libraries from both Homebrew installations
ARM64_LCMS2="/opt/homebrew/opt/little-cms2/lib/liblcms2.2.dylib"
X86_LCMS2="/usr/local/opt/little-cms2/lib/liblcms2.2.dylib"
ARM64_LIBPNG="/opt/homebrew/opt/libpng/lib/libpng16.16.dylib"
X86_LIBPNG="/usr/local/opt/libpng/lib/libpng16.16.dylib"

# Check if libraries exist
for lib in "$ARM64_LCMS2" "$X86_LCMS2" "$ARM64_LIBPNG" "$X86_LIBPNG"; do
    if [ ! -f "$lib" ]; then
        echo "ERROR: Library not found at $lib"
        echo "Ensure both arm64 and x86_64 Homebrew have libpng and little-cms2 installed."
        exit 1
    fi
done

# Create universal dylibs via lipo
echo "Creating universal liblcms2.2.dylib..."
lipo -create "$ARM64_LCMS2" "$X86_LCMS2" -output "$MACOS_DIR/liblcms2.2.dylib"

echo "Creating universal libpng16.16.dylib..."
lipo -create "$ARM64_LIBPNG" "$X86_LIBPNG" -output "$MACOS_DIR/libpng16.16.dylib"

# Fix library paths in pngquant to use @executable_path (both arch paths)
echo "Fixing library paths in pngquant..."
install_name_tool -change "/opt/homebrew/opt/little-cms2/lib/liblcms2.2.dylib" "@executable_path/liblcms2.2.dylib" "$PNGQUANT"
install_name_tool -change "/usr/local/opt/little-cms2/lib/liblcms2.2.dylib" "@executable_path/liblcms2.2.dylib" "$PNGQUANT"
install_name_tool -change "/opt/homebrew/opt/libpng/lib/libpng16.16.dylib" "@executable_path/libpng16.16.dylib" "$PNGQUANT"
install_name_tool -change "/usr/local/opt/libpng/lib/libpng16.16.dylib" "@executable_path/libpng16.16.dylib" "$PNGQUANT"

# Fix the library IDs to be relative (for proper signing)
echo "Fixing library IDs..."
install_name_tool -id "@executable_path/liblcms2.2.dylib" "$MACOS_DIR/liblcms2.2.dylib"
install_name_tool -id "@executable_path/libpng16.16.dylib" "$MACOS_DIR/libpng16.16.dylib"

echo ""
echo "=== Verifying ==="
echo "pngquant dependencies:"
otool -L "$PNGQUANT" | grep -E "lcms|libpng"

echo ""
echo "liblcms2.2.dylib architectures:"
file "$MACOS_DIR/liblcms2.2.dylib"

echo "libpng16.16.dylib architectures:"
file "$MACOS_DIR/libpng16.16.dylib"

echo ""
echo "=== Done ==="
echo "Universal libraries bundled. Now run sign-for-notarization.sh to sign everything."
