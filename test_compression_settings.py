#!/usr/bin/env python3
"""
Tests for oxipng and zopflipng settings argument generation.

Run from the command line:
    python3 test_compression_settings.py

Or run the app and use the test menu (if added).
"""

import sys
import os

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


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("Running compression settings tests")
    print("=" * 60 + "\n")

    result = TestResult()

    print("oxipng tests:")
    print("-" * 40)
    test_oxipng_defaults(result)
    test_oxipng_max_optimization(result)
    test_oxipng_optimization_levels(result)
    test_oxipng_strip_metadata(result)
    test_oxipng_alpha_optimization(result)
    test_oxipng_interlace(result)
    test_oxipng_threads(result)
    test_oxipng_timeout(result)

    print("\nzopflipng tests:")
    print("-" * 40)
    test_zopflipng_defaults(result)
    test_zopflipng_iterations(result)
    test_zopflipng_max_compression(result)
    test_zopflipng_quick_mode(result)
    test_zopflipng_keep_chunks(result)

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
