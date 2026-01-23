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
fi

echo ""
echo "=== Step 8: Sign Python.framework ==="
sign_item "$PYFRAMEWORK"

echo ""
echo "=== Step 9: Sign CLI tools ==="
[ -f "$APP/Contents/MacOS/pngquant" ] && sign_item "$APP/Contents/MacOS/pngquant"
[ -f "$APP/Contents/MacOS/oxipng" ] && sign_item "$APP/Contents/MacOS/oxipng"
[ -f "$APP/Contents/MacOS/zopflipng" ] && sign_item "$APP/Contents/MacOS/zopflipng"

echo ""
echo "=== Step 10: Sign main app bundle ==="
sign_item "$APP"

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
