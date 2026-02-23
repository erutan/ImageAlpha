#!/bin/bash
set -euo pipefail

# This script signs an ImageAlpha.app bundle for notarization
# Usage: ./sign-for-notarization.sh /path/to/ImageAlpha.app

if [ $# -ne 1 ]; then
    echo "Usage: $0 /path/to/ImageAlpha.app"
    exit 1
fi

APP="$1"

if [ ! -d "$APP" ]; then
    echo "ERROR: App bundle not found: $APP"
    exit 1
fi

echo "=== Signing $APP for Notarization ==="

# Step 0: Remove __pycache__ directories to prevent bytecode from breaking signature
echo ""
echo "=== Step 0: Removing Python bytecode cache ==="
find "$APP" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$APP" -type f -name "*.pyc" -delete 2>/dev/null || true
echo "  Removed __pycache__ directories and .pyc files"

# Step 0.5: Bundle pngquant's Homebrew library dependencies (universal)
echo ""
echo "=== Step 0.5: Bundling universal pngquant libraries ==="
MACOS_DIR="$APP/Contents/MacOS"
PNGQUANT="$MACOS_DIR/pngquant"
ARM64_LCMS2="/opt/homebrew/opt/little-cms2/lib/liblcms2.2.dylib"
X86_LCMS2="/usr/local/opt/little-cms2/lib/liblcms2.2.dylib"
ARM64_LIBPNG="/opt/homebrew/opt/libpng/lib/libpng16.16.dylib"
X86_LIBPNG="/usr/local/opt/libpng/lib/libpng16.16.dylib"

if [ -f "$PNGQUANT" ] && [ -f "$ARM64_LCMS2" ] && [ -f "$X86_LCMS2" ] && [ -f "$ARM64_LIBPNG" ] && [ -f "$X86_LIBPNG" ]; then
    # Check if pngquant still references Homebrew paths (not already bundled)
    if otool -L "$PNGQUANT" | grep -qE "/opt/homebrew|/usr/local/opt"; then
        echo "  Creating universal liblcms2.2.dylib..."
        lipo -create "$ARM64_LCMS2" "$X86_LCMS2" -output "$MACOS_DIR/liblcms2.2.dylib"
        echo "  Creating universal libpng16.16.dylib..."
        lipo -create "$ARM64_LIBPNG" "$X86_LIBPNG" -output "$MACOS_DIR/libpng16.16.dylib"
        echo "  Fixing library paths in pngquant..."
        install_name_tool -change "/opt/homebrew/opt/little-cms2/lib/liblcms2.2.dylib" "@executable_path/liblcms2.2.dylib" "$PNGQUANT"
        install_name_tool -change "/usr/local/opt/little-cms2/lib/liblcms2.2.dylib" "@executable_path/liblcms2.2.dylib" "$PNGQUANT"
        install_name_tool -change "/opt/homebrew/opt/libpng/lib/libpng16.16.dylib" "@executable_path/libpng16.16.dylib" "$PNGQUANT"
        install_name_tool -change "/usr/local/opt/libpng/lib/libpng16.16.dylib" "@executable_path/libpng16.16.dylib" "$PNGQUANT"
        echo "  Fixing library IDs..."
        install_name_tool -id "@executable_path/liblcms2.2.dylib" "$MACOS_DIR/liblcms2.2.dylib"
        install_name_tool -id "@executable_path/libpng16.16.dylib" "$MACOS_DIR/libpng16.16.dylib"
        echo "  Universal libraries bundled successfully"
    else
        echo "  Libraries already bundled (pngquant doesn't reference Homebrew paths)"
    fi
else
    echo "  Skipping library bundling (pngquant or Homebrew libs not found on both architectures)"
fi

# Find Developer ID Application certificate
IDENTITY=$(security find-identity -v -p codesigning | grep "Developer ID Application" | head -1 | sed 's/.*"\(.*\)".*/\1/')
if [ -z "$IDENTITY" ]; then
    echo "ERROR: No Developer ID Application certificate found"
    exit 1
fi
echo "Using identity: $IDENTITY"

sign_item() {
    echo "  Signing: $1"
    codesign --force --options runtime --timestamp --sign "$IDENTITY" "$1" || {
        echo "    ERROR: Failed to sign $1"
        return 1
    }
}

PYFRAMEWORK="$APP/Contents/Frameworks/Python.framework"
PYVER="$PYFRAMEWORK/Versions/3.13"

echo ""
echo "=== Step 1: Sign .so files ==="
find "$PYVER/lib" -type f -name "*.so" | while read -r f; do
    sign_item "$f"
done

echo ""
echo "=== Step 2: Sign .dylib files ==="
find "$PYVER/lib" -type f -name "*.dylib" | while read -r f; do
    sign_item "$f"
done

echo ""
echo "=== Step 3: Sign .o files ==="
find "$PYVER/lib" -type f -name "*.o" | while read -r f; do
    sign_item "$f"
done

echo ""
echo "=== Step 4: Sign Tcl.framework (inside-out) ==="
TCL="$PYVER/Frameworks/Tcl.framework"
if [ -d "$TCL" ]; then
    # Sign .a files inside Tcl.framework first
    find "$TCL" -type f -name "*.a" | while read -r f; do
        sign_item "$f"
    done
    [ -f "$TCL/Versions/8.6/Tcl" ] && sign_item "$TCL/Versions/8.6/Tcl"
    sign_item "$TCL"
fi

echo ""
echo "=== Step 5: Sign Tk.framework (inside-out) ==="
TK="$PYVER/Frameworks/Tk.framework"
if [ -d "$TK" ]; then
    # Sign .a files inside Tk.framework first
    find "$TK" -type f -name "*.a" | while read -r f; do
        sign_item "$f"
    done
    [ -f "$TK/Versions/8.6/Tk" ] && sign_item "$TK/Versions/8.6/Tk"
    sign_item "$TK"
fi

echo ""
echo "=== Step 6: Sign Python binaries ==="
[ -f "$PYVER/bin/python3.13" ] && sign_item "$PYVER/bin/python3.13"
[ -f "$PYVER/bin/python3.13-intel64" ] && sign_item "$PYVER/bin/python3.13-intel64"
[ -f "$PYVER/Python" ] && sign_item "$PYVER/Python"

echo ""
echo "=== Step 7: Sign Python.app (inside-out) ==="
PYAPP="$PYVER/Resources/Python.app"
if [ -d "$PYAPP" ]; then
    [ -f "$PYAPP/Contents/MacOS/Python" ] && sign_item "$PYAPP/Contents/MacOS/Python"
    sign_item "$PYAPP"
else
    echo "  Python.app not present (removed by strip phase) - skipping"
fi

echo ""
echo "=== Step 8: Sign Python.framework ==="
sign_item "$PYFRAMEWORK"

echo ""
echo "=== Step 9: Sign bundled libraries ==="
# These are bundled Homebrew libraries for pngquant
[ -f "$APP/Contents/MacOS/liblcms2.2.dylib" ] && sign_item "$APP/Contents/MacOS/liblcms2.2.dylib"
[ -f "$APP/Contents/MacOS/libpng16.16.dylib" ] && sign_item "$APP/Contents/MacOS/libpng16.16.dylib"

echo ""
echo "=== Step 10: Sign CLI tools (with entitlements) ==="
# CLI tools run as subprocesses and need their own entitlements
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENTITLEMENTS="$SCRIPT_DIR/ImageAlpha.entitlements"
sign_cli_tool() {
    if [ -f "$1" ]; then
        echo "  Signing with entitlements: $1"
        if [ -f "$ENTITLEMENTS" ]; then
            codesign --force --options runtime --timestamp --entitlements "$ENTITLEMENTS" --sign "$IDENTITY" "$1" || {
                echo "    ERROR: Failed to sign $1"
                return 1
            }
        else
            sign_item "$1"
        fi
    fi
}
sign_cli_tool "$APP/Contents/MacOS/pngquant"
sign_cli_tool "$APP/Contents/MacOS/posterize"
sign_cli_tool "$APP/Contents/MacOS/oxipng"
sign_cli_tool "$APP/Contents/MacOS/zopflipng"

echo ""
echo "=== Step 10: Sign main app bundle (with entitlements) ==="
if [ -f "$ENTITLEMENTS" ]; then
    echo "  Using entitlements: $ENTITLEMENTS"
    codesign --force --options runtime --timestamp --entitlements "$ENTITLEMENTS" --sign "$IDENTITY" "$APP" || {
        echo "    ERROR: Failed to sign $APP"
        exit 1
    }
else
    echo "  WARNING: Entitlements file not found, signing without entitlements"
    sign_item "$APP"
fi

echo ""
echo "=== Verifying signature ==="
codesign --verify --deep --strict "$APP" && echo "PASSED" || echo "FAILED"

echo ""
echo "=== Checking for unsigned Mach-O files ==="
find "$APP" -type f \( -name "*.so" -o -name "*.dylib" -o -name "*.o" \) -exec sh -c 'codesign -dvv "$1" 2>/dev/null || echo "UNSIGNED: $1"' _ {} \;

echo ""
echo "=== Done ==="
echo "If verification passed, you can submit with:"
echo "  xcrun notarytool submit \"$APP\" --keychain-profile ImageAlpha --wait"
