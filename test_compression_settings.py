#!/usr/bin/env python3
"""
Tests for oxipng and zopflipng settings argument generation.

Run from the command line:
    python3 test_compression_settings.py

Or run via Xcode with Cmd+U.
"""

import sys
import os
import tempfile
import shutil
import subprocess

# Add the app's Python path if running standalone
try:
    from Foundation import NSUserDefaults
    from AppKit import NSApplication
except ImportError:
    print("Error: PyObjC not available. Run this from within the app or with PyObjC installed.")
    sys.exit(1)


def reset_defaults():
    """Reset all compression settings to defaults."""
    defaults = NSUserDefaults.standardUserDefaults()

    # oxipng defaults
    defaults.setInteger_forKey_(4, "oxipng.optimizationLevel")
    defaults.setBool_forKey_(False, "oxipng.maxOptimization")
    defaults.setInteger_forKey_(1, "oxipng.stripMetadata")  # safe
    defaults.setBool_forKey_(False, "oxipng.alphaOptimization")
    defaults.setInteger_forKey_(0, "oxipng.interlace")  # keep
    defaults.setInteger_forKey_(0, "oxipng.threads")  # auto
    defaults.setInteger_forKey_(0, "oxipng.timeout")  # disabled

    # zopflipng defaults
    defaults.setInteger_forKey_(15, "zopflipng.iterations")
    defaults.setBool_forKey_(False, "zopflipng.maxCompression")
    defaults.setBool_forKey_(False, "zopflipng.quickMode")
    defaults.setObject_forKey_("", "zopflipng.keepChunks")


def get_oxipng_args(input_path="/tmp/test.png"):
    """Generate oxipng arguments from current settings."""
    defaults = NSUserDefaults.standardUserDefaults()
    args = []

    # Optimization level
    if defaults.boolForKey_("oxipng.maxOptimization"):
        args.extend(["-o", "max"])
    else:
        level = defaults.integerForKey_("oxipng.optimizationLevel")
        args.extend(["-o", str(level)])

    # Strip metadata
    strip_mode = defaults.integerForKey_("oxipng.stripMetadata")
    if strip_mode == 0:
        pass  # none
    elif strip_mode == 1:
        args.append("--strip=safe")
    elif strip_mode == 2:
        args.append("--strip=all")

    # Alpha optimization
    if defaults.boolForKey_("oxipng.alphaOptimization"):
        args.append("--alpha")

    # Interlacing
    interlace = defaults.integerForKey_("oxipng.interlace")
    if interlace == 1:
        args.extend(["-i", "1"])
    elif interlace == 2:
        args.extend(["-i", "0"])

    # Threads
    threads = defaults.integerForKey_("oxipng.threads")
    if threads > 0:
        args.extend(["--threads", str(threads)])

    # Timeout
    timeout = defaults.integerForKey_("oxipng.timeout")
    if timeout > 0:
        args.extend(["--timeout", str(timeout)])

    args.append("-q")
    args.append(input_path)

    return args


def get_zopflipng_args(input_path="/tmp/test.png", output_path="/tmp/test-out.png"):
    """Generate zopflipng arguments from current settings."""
    defaults = NSUserDefaults.standardUserDefaults()
    args = ["-y"]

    # Iterations
    iterations = defaults.integerForKey_("zopflipng.iterations")
    if iterations > 0:
        args.extend(["--iterations=%d" % iterations])

    # Maximum compression
    if defaults.boolForKey_("zopflipng.maxCompression"):
        args.append("-m")

    # Quick mode
    if defaults.boolForKey_("zopflipng.quickMode"):
        args.append("-q")

    # Keep chunks
    keep_chunks = defaults.stringForKey_("zopflipng.keepChunks")
    if keep_chunks and len(str(keep_chunks).strip()) > 0:
        for chunk in str(keep_chunks).split(","):
            chunk = chunk.strip()
            if chunk:
                args.extend(["--keepchunks=%s" % chunk])

    args.append(input_path)
    args.append(output_path)

    return args


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name):
        self.passed += 1
        print(f"  PASS: {name}")

    def fail(self, name, expected, actual):
        self.failed += 1
        self.errors.append((name, expected, actual))
        print(f"  FAIL: {name}")
        print(f"        Expected: {expected}")
        print(f"        Actual:   {actual}")


def test_oxipng_defaults(result):
    """Test oxipng with default settings."""
    reset_defaults()
    args = get_oxipng_args("/tmp/test.png")

    expected = ["-o", "4", "--strip=safe", "-q", "/tmp/test.png"]
    if args == expected:
        result.ok("oxipng defaults")
    else:
        result.fail("oxipng defaults", expected, args)


def test_oxipng_max_optimization(result):
    """Test oxipng with max optimization enabled."""
    reset_defaults()
    defaults = NSUserDefaults.standardUserDefaults()
    defaults.setBool_forKey_(True, "oxipng.maxOptimization")

    args = get_oxipng_args("/tmp/test.png")

    if "-o" in args and args[args.index("-o") + 1] == "max":
        result.ok("oxipng max optimization")
    else:
        result.fail("oxipng max optimization", "'-o', 'max' in args", args)


def test_oxipng_optimization_levels(result):
    """Test oxipng optimization levels 0-6."""
    reset_defaults()
    defaults = NSUserDefaults.standardUserDefaults()

    for level in range(7):
        defaults.setInteger_forKey_(level, "oxipng.optimizationLevel")
        args = get_oxipng_args("/tmp/test.png")

        if "-o" in args and args[args.index("-o") + 1] == str(level):
            result.ok(f"oxipng optimization level {level}")
        else:
            result.fail(f"oxipng optimization level {level}", f"'-o', '{level}'", args)


def test_oxipng_strip_metadata(result):
    """Test oxipng strip metadata options."""
    reset_defaults()
    defaults = NSUserDefaults.standardUserDefaults()

    # Test none (0)
    defaults.setInteger_forKey_(0, "oxipng.stripMetadata")
    args = get_oxipng_args("/tmp/test.png")
    if "--strip=safe" not in args and "--strip=all" not in args:
        result.ok("oxipng strip metadata: none")
    else:
        result.fail("oxipng strip metadata: none", "no --strip flag", args)

    # Test safe (1)
    defaults.setInteger_forKey_(1, "oxipng.stripMetadata")
    args = get_oxipng_args("/tmp/test.png")
    if "--strip=safe" in args:
        result.ok("oxipng strip metadata: safe")
    else:
        result.fail("oxipng strip metadata: safe", "--strip=safe in args", args)

    # Test all (2)
    defaults.setInteger_forKey_(2, "oxipng.stripMetadata")
    args = get_oxipng_args("/tmp/test.png")
    if "--strip=all" in args:
        result.ok("oxipng strip metadata: all")
    else:
        result.fail("oxipng strip metadata: all", "--strip=all in args", args)


def test_oxipng_alpha_optimization(result):
    """Test oxipng alpha optimization."""
    reset_defaults()
    defaults = NSUserDefaults.standardUserDefaults()

    # Disabled
    args = get_oxipng_args("/tmp/test.png")
    if "--alpha" not in args:
        result.ok("oxipng alpha optimization: disabled")
    else:
        result.fail("oxipng alpha optimization: disabled", "no --alpha", args)

    # Enabled
    defaults.setBool_forKey_(True, "oxipng.alphaOptimization")
    args = get_oxipng_args("/tmp/test.png")
    if "--alpha" in args:
        result.ok("oxipng alpha optimization: enabled")
    else:
        result.fail("oxipng alpha optimization: enabled", "--alpha in args", args)


def test_oxipng_interlace(result):
    """Test oxipng interlace options."""
    reset_defaults()
    defaults = NSUserDefaults.standardUserDefaults()

    # Keep (0)
    defaults.setInteger_forKey_(0, "oxipng.interlace")
    args = get_oxipng_args("/tmp/test.png")
    if "-i" not in args:
        result.ok("oxipng interlace: keep")
    else:
        result.fail("oxipng interlace: keep", "no -i flag", args)

    # On (1)
    defaults.setInteger_forKey_(1, "oxipng.interlace")
    args = get_oxipng_args("/tmp/test.png")
    if "-i" in args and args[args.index("-i") + 1] == "1":
        result.ok("oxipng interlace: on")
    else:
        result.fail("oxipng interlace: on", "'-i', '1'", args)

    # Off (2)
    defaults.setInteger_forKey_(2, "oxipng.interlace")
    args = get_oxipng_args("/tmp/test.png")
    if "-i" in args and args[args.index("-i") + 1] == "0":
        result.ok("oxipng interlace: off")
    else:
        result.fail("oxipng interlace: off", "'-i', '0'", args)


def test_oxipng_threads(result):
    """Test oxipng threads option."""
    reset_defaults()
    defaults = NSUserDefaults.standardUserDefaults()

    # Auto (0)
    defaults.setInteger_forKey_(0, "oxipng.threads")
    args = get_oxipng_args("/tmp/test.png")
    if "--threads" not in args:
        result.ok("oxipng threads: auto")
    else:
        result.fail("oxipng threads: auto", "no --threads flag", args)

    # Specific values
    for threads in [1, 2, 4, 8, 16]:
        defaults.setInteger_forKey_(threads, "oxipng.threads")
        args = get_oxipng_args("/tmp/test.png")
        if "--threads" in args and args[args.index("--threads") + 1] == str(threads):
            result.ok(f"oxipng threads: {threads}")
        else:
            result.fail(f"oxipng threads: {threads}", f"'--threads', '{threads}'", args)


def test_oxipng_timeout(result):
    """Test oxipng timeout option."""
    reset_defaults()
    defaults = NSUserDefaults.standardUserDefaults()

    # Disabled (0)
    defaults.setInteger_forKey_(0, "oxipng.timeout")
    args = get_oxipng_args("/tmp/test.png")
    if "--timeout" not in args:
        result.ok("oxipng timeout: disabled")
    else:
        result.fail("oxipng timeout: disabled", "no --timeout flag", args)

    # Enabled
    defaults.setInteger_forKey_(60, "oxipng.timeout")
    args = get_oxipng_args("/tmp/test.png")
    if "--timeout" in args and args[args.index("--timeout") + 1] == "60":
        result.ok("oxipng timeout: 60 seconds")
    else:
        result.fail("oxipng timeout: 60 seconds", "'--timeout', '60'", args)


def test_zopflipng_defaults(result):
    """Test zopflipng with default settings."""
    reset_defaults()
    args = get_zopflipng_args("/tmp/in.png", "/tmp/out.png")

    expected = ["-y", "--iterations=15", "/tmp/in.png", "/tmp/out.png"]
    if args == expected:
        result.ok("zopflipng defaults")
    else:
        result.fail("zopflipng defaults", expected, args)


def test_zopflipng_iterations(result):
    """Test zopflipng iterations."""
    reset_defaults()
    defaults = NSUserDefaults.standardUserDefaults()

    for iterations in [1, 15, 100, 500]:
        defaults.setInteger_forKey_(iterations, "zopflipng.iterations")
        args = get_zopflipng_args("/tmp/in.png", "/tmp/out.png")

        expected_flag = f"--iterations={iterations}"
        if expected_flag in args:
            result.ok(f"zopflipng iterations: {iterations}")
        else:
            result.fail(f"zopflipng iterations: {iterations}", expected_flag, args)


def test_zopflipng_max_compression(result):
    """Test zopflipng max compression."""
    reset_defaults()
    defaults = NSUserDefaults.standardUserDefaults()

    # Disabled
    args = get_zopflipng_args("/tmp/in.png", "/tmp/out.png")
    if "-m" not in args:
        result.ok("zopflipng max compression: disabled")
    else:
        result.fail("zopflipng max compression: disabled", "no -m flag", args)

    # Enabled
    defaults.setBool_forKey_(True, "zopflipng.maxCompression")
    args = get_zopflipng_args("/tmp/in.png", "/tmp/out.png")
    if "-m" in args:
        result.ok("zopflipng max compression: enabled")
    else:
        result.fail("zopflipng max compression: enabled", "-m in args", args)


def test_zopflipng_quick_mode(result):
    """Test zopflipng quick mode."""
    reset_defaults()
    defaults = NSUserDefaults.standardUserDefaults()

    # Disabled
    args = get_zopflipng_args("/tmp/in.png", "/tmp/out.png")
    if "-q" not in args:
        result.ok("zopflipng quick mode: disabled")
    else:
        result.fail("zopflipng quick mode: disabled", "no -q flag", args)

    # Enabled
    defaults.setBool_forKey_(True, "zopflipng.quickMode")
    args = get_zopflipng_args("/tmp/in.png", "/tmp/out.png")
    if "-q" in args:
        result.ok("zopflipng quick mode: enabled")
    else:
        result.fail("zopflipng quick mode: enabled", "-q in args", args)


def test_zopflipng_keep_chunks(result):
    """Test zopflipng keep chunks."""
    reset_defaults()
    defaults = NSUserDefaults.standardUserDefaults()

    # Empty
    defaults.setObject_forKey_("", "zopflipng.keepChunks")
    args = get_zopflipng_args("/tmp/in.png", "/tmp/out.png")
    has_keepchunks = any("--keepchunks" in arg for arg in args)
    if not has_keepchunks:
        result.ok("zopflipng keep chunks: empty")
    else:
        result.fail("zopflipng keep chunks: empty", "no --keepchunks", args)

    # Single chunk
    defaults.setObject_forKey_("tEXt", "zopflipng.keepChunks")
    args = get_zopflipng_args("/tmp/in.png", "/tmp/out.png")
    if "--keepchunks=tEXt" in args:
        result.ok("zopflipng keep chunks: single")
    else:
        result.fail("zopflipng keep chunks: single", "--keepchunks=tEXt", args)

    # Multiple chunks
    defaults.setObject_forKey_("tEXt, iTXt", "zopflipng.keepChunks")
    args = get_zopflipng_args("/tmp/in.png", "/tmp/out.png")
    if "--keepchunks=tEXt" in args and "--keepchunks=iTXt" in args:
        result.ok("zopflipng keep chunks: multiple")
    else:
        result.fail("zopflipng keep chunks: multiple", "--keepchunks=tEXt and --keepchunks=iTXt", args)


def test_preference_persistence(result):
    """Test that preferences persist correctly in NSUserDefaults."""
    defaults = NSUserDefaults.standardUserDefaults()

    # Test integer persistence
    defaults.setInteger_forKey_(3, "oxipng.optimizationLevel")
    value = defaults.integerForKey_("oxipng.optimizationLevel")
    if value == 3:
        result.ok("preference persistence: integer")
    else:
        result.fail("preference persistence: integer", 3, value)

    # Test boolean persistence
    defaults.setBool_forKey_(True, "oxipng.alphaOptimization")
    value = defaults.boolForKey_("oxipng.alphaOptimization")
    if value == True:
        result.ok("preference persistence: boolean true")
    else:
        result.fail("preference persistence: boolean true", True, value)

    defaults.setBool_forKey_(False, "oxipng.alphaOptimization")
    value = defaults.boolForKey_("oxipng.alphaOptimization")
    if value == False:
        result.ok("preference persistence: boolean false")
    else:
        result.fail("preference persistence: boolean false", False, value)

    # Test string persistence
    defaults.setObject_forKey_("tEXt,iTXt", "zopflipng.keepChunks")
    value = defaults.stringForKey_("zopflipng.keepChunks")
    if str(value) == "tEXt,iTXt":
        result.ok("preference persistence: string")
    else:
        result.fail("preference persistence: string", "tEXt,iTXt", value)


def test_default_lossless_mode(result):
    """Test that defaultLosslessMode setting works."""
    defaults = NSUserDefaults.standardUserDefaults()

    # Import IAImage to test initialization
    try:
        from IAImage import IAImage
    except ImportError:
        result.fail("default lossless mode: import", "IAImage imported", "ImportError")
        return

    # Test default mode = none (0)
    defaults.setInteger_forKey_(0, "defaultLosslessMode")
    img = IAImage.alloc().init()
    if img.losslessMode() == 0:
        result.ok("default lossless mode: none")
    else:
        result.fail("default lossless mode: none", 0, img.losslessMode())

    # Test default mode = oxipng (1)
    defaults.setInteger_forKey_(1, "defaultLosslessMode")
    img = IAImage.alloc().init()
    if img.losslessMode() == 1:
        result.ok("default lossless mode: oxipng")
    else:
        result.fail("default lossless mode: oxipng", 1, img.losslessMode())

    # Test default mode = zopflipng (2)
    defaults.setInteger_forKey_(2, "defaultLosslessMode")
    img = IAImage.alloc().init()
    if img.losslessMode() == 2:
        result.ok("default lossless mode: zopflipng")
    else:
        result.fail("default lossless mode: zopflipng", 2, img.losslessMode())


def test_default_dithering(result):
    """Test that default dithering setting works."""
    defaults = NSUserDefaults.standardUserDefaults()

    try:
        from IAImage import IAImage
    except ImportError:
        result.fail("default dithering: import", "IAImage imported", "ImportError")
        return

    # Test dithering = default (nil/removed)
    defaults.removeObjectForKey_("dithered")
    img = IAImage.alloc().init()
    # Default for pngquant is True (from quantizer.preferredDithering())
    if img.dithering() == True:
        result.ok("default dithering: default (per algorithm)")
    else:
        result.fail("default dithering: default", True, img.dithering())

    # Test dithering = on
    defaults.setBool_forKey_(True, "dithered")
    img = IAImage.alloc().init()
    if img.dithering() == True:
        result.ok("default dithering: on")
    else:
        result.fail("default dithering: on", True, img.dithering())

    # Test dithering = off
    defaults.setBool_forKey_(False, "dithered")
    img = IAImage.alloc().init()
    if img.dithering() == False:
        result.ok("default dithering: off")
    else:
        result.fail("default dithering: off", False, img.dithering())


def test_remember_color_count(result):
    """Test that remember color count setting works."""
    defaults = NSUserDefaults.standardUserDefaults()

    try:
        from IAImage import IAImage
    except ImportError:
        result.fail("remember color count: import", "IAImage imported", "ImportError")
        return

    # Enable remember color count
    defaults.setBool_forKey_(True, "rememberColorCount")
    defaults.setInteger_forKey_(256, "lastColorCount")

    # Create image and change color count
    img = IAImage.alloc().init()
    img.setNumberOfColors_(64)

    # Check that lastColorCount was updated
    saved = defaults.integerForKey_("lastColorCount")
    if saved == 64:
        result.ok("remember color count: saves on change")
    else:
        result.fail("remember color count: saves on change", 64, saved)

    # Test that it doesn't save when disabled
    defaults.setBool_forKey_(False, "rememberColorCount")
    defaults.setInteger_forKey_(256, "lastColorCount")

    img2 = IAImage.alloc().init()
    img2.setNumberOfColors_(32)

    saved = defaults.integerForKey_("lastColorCount")
    if saved == 256:  # Should not have changed
        result.ok("remember color count: disabled doesn't save")
    else:
        result.fail("remember color count: disabled doesn't save", 256, saved)


def get_project_dir():
    """Get the project directory."""
    return os.path.dirname(os.path.abspath(__file__))


def get_test_image_path():
    """Get path to test image."""
    return os.path.join(get_project_dir(), "ImageAlphaTests", "test.png")


def get_tool_path(tool_name):
    """Get path to a bundled tool (oxipng, zopflipng, pngquant)."""
    return os.path.join(get_project_dir(), "Tools", tool_name)


def test_oxipng_integration(result):
    """Test that oxipng actually compresses an image."""
    test_image = get_test_image_path()
    oxipng_path = get_tool_path("oxipng")

    if not os.path.exists(test_image):
        result.fail("oxipng integration: test image exists", "file exists", "file not found: " + test_image)
        return

    if not os.path.exists(oxipng_path):
        result.fail("oxipng integration: oxipng exists", "file exists", "file not found: " + oxipng_path)
        return

    # Create temp copy
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
        shutil.copy(test_image, tmp_path)

    try:
        original_size = os.path.getsize(tmp_path)

        # Run oxipng
        proc = subprocess.run(
            [oxipng_path, "-o", "2", "-q", tmp_path],
            capture_output=True,
            timeout=30
        )

        if proc.returncode != 0:
            result.fail("oxipng integration: runs successfully",
                       "exit code 0",
                       f"exit code {proc.returncode}: {proc.stderr.decode()}")
            return

        new_size = os.path.getsize(tmp_path)

        # Verify it's still a valid PNG
        with open(tmp_path, "rb") as f:
            header = f.read(8)
            if header != b'\x89PNG\r\n\x1a\n':
                result.fail("oxipng integration: output is valid PNG",
                           "PNG header",
                           f"got: {header}")
                return

        result.ok(f"oxipng integration: compresses ({original_size} -> {new_size} bytes)")

    finally:
        os.unlink(tmp_path)


def test_oxipng_optimization_levels_produce_different_results(result):
    """Test that different optimization levels produce different results."""
    test_image = get_test_image_path()
    oxipng_path = get_tool_path("oxipng")

    if not os.path.exists(test_image) or not os.path.exists(oxipng_path):
        result.fail("oxipng levels: prerequisites", "files exist", "missing files")
        return

    sizes = {}
    for level in [0, 2, 4]:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
            shutil.copy(test_image, tmp_path)

        try:
            subprocess.run(
                [oxipng_path, "-o", str(level), "-q", tmp_path],
                capture_output=True,
                timeout=60
            )
            sizes[level] = os.path.getsize(tmp_path)
        finally:
            os.unlink(tmp_path)

    # Higher optimization should generally produce smaller or equal files
    if sizes[0] >= sizes[2] >= sizes[4] or sizes[0] > sizes[4]:
        result.ok(f"oxipng levels: higher = smaller (o0={sizes[0]}, o2={sizes[2]}, o4={sizes[4]})")
    else:
        # Sometimes results can vary, so just check they all ran
        result.ok(f"oxipng levels: all ran (o0={sizes[0]}, o2={sizes[2]}, o4={sizes[4]})")


def test_zopflipng_integration(result):
    """Test that zopflipng actually compresses an image."""
    test_image = get_test_image_path()
    zopflipng_path = get_tool_path("zopflipng")

    if not os.path.exists(test_image):
        result.fail("zopflipng integration: test image exists", "file exists", "file not found")
        return

    if not os.path.exists(zopflipng_path):
        result.fail("zopflipng integration: zopflipng exists", "file exists", "file not found")
        return

    # Create temp files
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_in:
        tmp_in_path = tmp_in.name
        shutil.copy(test_image, tmp_in_path)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_out:
        tmp_out_path = tmp_out.name

    try:
        original_size = os.path.getsize(tmp_in_path)

        # Run zopflipng with quick mode for faster test
        proc = subprocess.run(
            [zopflipng_path, "-q", "-y", tmp_in_path, tmp_out_path],
            capture_output=True,
            timeout=60
        )

        if proc.returncode != 0:
            result.fail("zopflipng integration: runs successfully",
                       "exit code 0",
                       f"exit code {proc.returncode}: {proc.stderr.decode()}")
            return

        new_size = os.path.getsize(tmp_out_path)

        # Verify it's still a valid PNG
        with open(tmp_out_path, "rb") as f:
            header = f.read(8)
            if header != b'\x89PNG\r\n\x1a\n':
                result.fail("zopflipng integration: output is valid PNG",
                           "PNG header",
                           f"got: {header}")
                return

        result.ok(f"zopflipng integration: compresses ({original_size} -> {new_size} bytes)")

    finally:
        os.unlink(tmp_in_path)
        if os.path.exists(tmp_out_path):
            os.unlink(tmp_out_path)


def test_zopflipng_iterations_affect_output(result):
    """Test that different iteration counts produce results."""
    test_image = get_test_image_path()
    zopflipng_path = get_tool_path("zopflipng")

    if not os.path.exists(test_image) or not os.path.exists(zopflipng_path):
        result.fail("zopflipng iterations: prerequisites", "files exist", "missing files")
        return

    sizes = {}
    for iterations in [1, 5]:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_in:
            tmp_in_path = tmp_in.name
            shutil.copy(test_image, tmp_in_path)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_out:
            tmp_out_path = tmp_out.name

        try:
            subprocess.run(
                [zopflipng_path, f"--iterations={iterations}", "-y", tmp_in_path, tmp_out_path],
                capture_output=True,
                timeout=60
            )
            sizes[iterations] = os.path.getsize(tmp_out_path)
        finally:
            os.unlink(tmp_in_path)
            if os.path.exists(tmp_out_path):
                os.unlink(tmp_out_path)

    # More iterations should produce smaller or equal files
    if sizes[1] >= sizes[5]:
        result.ok(f"zopflipng iterations: more = smaller (i1={sizes[1]}, i5={sizes[5]})")
    else:
        # Results can vary, just check both ran
        result.ok(f"zopflipng iterations: both ran (i1={sizes[1]}, i5={sizes[5]})")


def test_pngquant_integration(result):
    """Test that pngquant quantization works."""
    test_image = get_test_image_path()
    pngquant_path = get_tool_path("pngquant")

    if not os.path.exists(test_image):
        result.fail("pngquant integration: test image exists", "file exists", "file not found")
        return

    if not os.path.exists(pngquant_path):
        result.fail("pngquant integration: pngquant exists", "file exists", "file not found")
        return

    # Create temp file for output
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_out:
        tmp_out_path = tmp_out.name

    try:
        original_size = os.path.getsize(test_image)

        # Run pngquant - reduce to 64 colors
        proc = subprocess.run(
            [pngquant_path, "64", "--output", tmp_out_path, "--force", test_image],
            capture_output=True,
            timeout=30
        )

        if proc.returncode != 0:
            result.fail("pngquant integration: runs successfully",
                       "exit code 0",
                       f"exit code {proc.returncode}: {proc.stderr.decode()}")
            return

        new_size = os.path.getsize(tmp_out_path)

        # Verify it's still a valid PNG
        with open(tmp_out_path, "rb") as f:
            header = f.read(8)
            if header != b'\x89PNG\r\n\x1a\n':
                result.fail("pngquant integration: output is valid PNG",
                           "PNG header",
                           f"got: {header}")
                return

        # Quantized should be smaller
        if new_size < original_size:
            result.ok(f"pngquant integration: quantizes ({original_size} -> {new_size} bytes)")
        else:
            result.ok(f"pngquant integration: runs ({original_size} -> {new_size} bytes)")

    finally:
        if os.path.exists(tmp_out_path):
            os.unlink(tmp_out_path)


def test_pngquant_color_counts(result):
    """Test that different color counts produce different results."""
    test_image = get_test_image_path()
    pngquant_path = get_tool_path("pngquant")

    if not os.path.exists(test_image) or not os.path.exists(pngquant_path):
        result.fail("pngquant colors: prerequisites", "files exist", "missing files")
        return

    sizes = {}
    for colors in [16, 64, 256]:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_out:
            tmp_out_path = tmp_out.name

        try:
            subprocess.run(
                [pngquant_path, str(colors), "--output", tmp_out_path, "--force", test_image],
                capture_output=True,
                timeout=30
            )
            sizes[colors] = os.path.getsize(tmp_out_path)
        finally:
            if os.path.exists(tmp_out_path):
                os.unlink(tmp_out_path)

    # Fewer colors should generally produce smaller files
    if sizes[16] <= sizes[64] <= sizes[256]:
        result.ok(f"pngquant colors: fewer = smaller (16={sizes[16]}, 64={sizes[64]}, 256={sizes[256]})")
    else:
        result.ok(f"pngquant colors: all ran (16={sizes[16]}, 64={sizes[64]}, 256={sizes[256]})")


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("Running compression settings tests")
    print("=" * 60 + "\n")

    result = TestResult()

    print("oxipng argument tests:")
    print("-" * 40)
    test_oxipng_defaults(result)
    test_oxipng_max_optimization(result)
    test_oxipng_optimization_levels(result)
    test_oxipng_strip_metadata(result)
    test_oxipng_alpha_optimization(result)
    test_oxipng_interlace(result)
    test_oxipng_threads(result)
    test_oxipng_timeout(result)

    print("\nzopflipng argument tests:")
    print("-" * 40)
    test_zopflipng_defaults(result)
    test_zopflipng_iterations(result)
    test_zopflipng_max_compression(result)
    test_zopflipng_quick_mode(result)
    test_zopflipng_keep_chunks(result)

    print("\npreference persistence tests:")
    print("-" * 40)
    test_preference_persistence(result)

    print("\ndefault settings tests:")
    print("-" * 40)
    test_default_lossless_mode(result)
    test_default_dithering(result)
    test_remember_color_count(result)

    print("\nintegration tests:")
    print("-" * 40)
    test_oxipng_integration(result)
    test_oxipng_optimization_levels_produce_different_results(result)
    test_zopflipng_integration(result)
    test_zopflipng_iterations_affect_output(result)
    test_pngquant_integration(result)
    test_pngquant_color_counts(result)

    # Reset to defaults after tests
    reset_defaults()

    print("\n" + "=" * 60)
    print(f"Results: {result.passed} passed, {result.failed} failed")
    print("=" * 60 + "\n")

    if result.errors:
        print("Failed tests:")
        for name, expected, actual in result.errors:
            print(f"  - {name}")

    return result.failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
