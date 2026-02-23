#!/bin/bash
set -euo pipefail

# This script builds universal (arm64 + x86_64) binaries for pngquant and posterize.
# Requires both arm64 (/opt/homebrew) and x86_64 (/usr/local) Homebrew installations
# with pngquant, libpng, and little-cms2 installed.
#
# Usage: ./build-universal-tools.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOOLS_DIR="$SCRIPT_DIR/Tools"

echo "=== Building universal Tools binaries ==="
echo ""

# --- Preflight checks ---

echo "=== Preflight: checking Homebrew installations ==="

if [ ! -x /opt/homebrew/bin/brew ]; then
    echo "ERROR: arm64 Homebrew not found at /opt/homebrew/bin/brew"
    exit 1
fi

if [ ! -x /usr/local/bin/brew ]; then
    echo "ERROR: x86_64 Homebrew not found at /usr/local/bin/brew"
    echo "Install with: arch -x86_64 /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# Ensure required packages are installed on both architectures
echo "Checking arm64 Homebrew packages..."
for pkg in pngquant libpng little-cms2; do
    if [ ! -d "/opt/homebrew/opt/$pkg" ]; then
        echo "  Installing $pkg (arm64)..."
        /opt/homebrew/bin/brew install "$pkg"
    else
        echo "  $pkg (arm64): OK"
    fi
done

echo "Checking x86_64 Homebrew packages..."
for pkg in pngquant libpng little-cms2; do
    if [ ! -d "/usr/local/opt/$pkg" ]; then
        echo "  Installing $pkg (x86_64)..."
        arch -x86_64 /usr/local/bin/brew install "$pkg"
    else
        echo "  $pkg (x86_64): OK"
    fi
done

echo ""

# --- pngquant ---

echo "=== Building universal pngquant ==="

ARM64_PNGQUANT="/opt/homebrew/bin/pngquant"
X86_PNGQUANT="/usr/local/bin/pngquant"

if [ ! -f "$ARM64_PNGQUANT" ]; then
    echo "ERROR: arm64 pngquant not found at $ARM64_PNGQUANT"
    exit 1
fi

if [ ! -f "$X86_PNGQUANT" ]; then
    echo "ERROR: x86_64 pngquant not found at $X86_PNGQUANT"
    exit 1
fi

echo "  Creating universal pngquant..."
lipo -create "$ARM64_PNGQUANT" "$X86_PNGQUANT" -output "$TOOLS_DIR/pngquant"
chmod +x "$TOOLS_DIR/pngquant"
echo "  Verifying:"
file "$TOOLS_DIR/pngquant"

echo ""

# --- posterize ---

echo "=== Building universal posterize ==="

POSTERIZE_SRC="/tmp/posterizer-src"

# Clone or update the source
if [ -d "$POSTERIZE_SRC" ]; then
    echo "  Updating existing posterizer source..."
    git -C "$POSTERIZE_SRC" pull --ff-only 2>/dev/null || true
else
    echo "  Cloning mediancut-posterizer..."
    git clone https://github.com/kornelski/mediancut-posterizer.git "$POSTERIZE_SRC"
fi

echo "  Building arm64..."
clang -O3 -arch arm64 -mmacosx-version-min=13.0 \
    -I/opt/homebrew/opt/libpng/include \
    "$POSTERIZE_SRC/posterize.c" "$POSTERIZE_SRC/rwpng.c" "$POSTERIZE_SRC/blurize.c" \
    /opt/homebrew/opt/libpng/lib/libpng16.a -lz \
    -o /tmp/posterize-arm64

echo "  Building x86_64..."
clang -O3 -arch x86_64 -mmacosx-version-min=13.0 \
    -I/usr/local/opt/libpng/include \
    "$POSTERIZE_SRC/posterize.c" "$POSTERIZE_SRC/rwpng.c" "$POSTERIZE_SRC/blurize.c" \
    /usr/local/opt/libpng/lib/libpng16.a -lz \
    -o /tmp/posterize-x86_64

echo "  Creating universal posterize..."
lipo -create /tmp/posterize-arm64 /tmp/posterize-x86_64 -output "$TOOLS_DIR/posterize"
chmod +x "$TOOLS_DIR/posterize"
echo "  Verifying:"
file "$TOOLS_DIR/posterize"

# Clean up temp build artifacts
rm -f /tmp/posterize-arm64 /tmp/posterize-x86_64

echo ""

# --- Summary ---

echo "=== Summary ==="
echo ""
echo "Tools directory:"
for tool in pngquant posterize oxipng zopflipng; do
    if [ -f "$TOOLS_DIR/$tool" ]; then
        echo "  $tool: $(file -b "$TOOLS_DIR/$tool" | head -1)"
    fi
done

echo ""
echo "pngquant dependencies:"
otool -L "$TOOLS_DIR/pngquant" | tail -n +2

echo ""
echo "posterize dependencies:"
otool -L "$TOOLS_DIR/posterize" | tail -n +2

echo ""
echo "=== Done ==="
echo "All tools are now universal binaries."
echo "Next: build in Xcode and verify with Activity Monitor (should show 'Apple' architecture)."
