# ImageAlpha Python 2 to Python 3 Migration Plan

**Project**: ImageAlpha
**Date Created**: 2025-12-28
**Current Status**: Python 2 (deprecated)
**Target**: Python 3.9+ with PyObjC
**Estimated Effort**: 2-4 days + testing
**Risk Level**: Medium

---

## Executive Summary

ImageAlpha is a macOS application (1,225 lines of Python code) that uses PyObjC to create a native Cocoa interface for PNG image optimization. The application was deprecated due to Python 2 end-of-life. This plan outlines a systematic migration to Python 3, updating all deprecated syntax, dependencies, and build configurations.

**Migration Feasibility**: ✅ **REASONABLE**
**Code Quality**: Good - minimal Python 2 idioms
**Main Challenges**: PyObjC compatibility, macOS framework integration, Xcode build system

---

## Table of Contents

1. [Pre-Migration Assessment](#1-pre-migration-assessment)
2. [Environment Setup](#2-environment-setup)
3. [Code Migration Steps](#3-code-migration-steps)
4. [Dependency Updates](#4-dependency-updates)
5. [Build System Updates](#5-build-system-updates)
6. [Testing Plan](#6-testing-plan)
7. [Rollback Strategy](#7-rollback-strategy)
8. [Post-Migration Tasks](#8-post-migration-tasks)
9. [Timeline](#9-timeline)

---

## 1. Pre-Migration Assessment

### 1.1 Current Architecture

**Technology Stack:**
- Python 2.x (system Python)
- PyObjC (Python-Objective-C bridge)
- macOS Frameworks: Foundation, AppKit, Quartz
- Build System: Xcode project
- External Tools: pngquant, pngnq, mediancut-posterizer

**File Inventory:**
```
Python Files (9 total, ~1,225 LOC):
├── main.py (29 lines) - Application entry point
├── ImageAlphaDocument.py (257 lines) - Document controller
├── IAImage.py (264 lines) - Image processing
├── IAImageView.py (249 lines) - Image viewer
├── IAImageViewInteractive.py (147 lines) - Interactive viewer
├── IASlider.py (85 lines) - Custom slider
├── IACollectionItem.py (164 lines) - Collection items
├── IABackgroundRenderer.py (30 lines) - Background rendering
└── Sparkle/objc_dep/objc_dep.py (266 lines) - Dependency analyzer
```

### 1.2 Identified Python 2 Issues

**CRITICAL (Must Fix):**

| File | Line | Issue | Python 3 Fix |
|------|------|-------|--------------|
| main.py | 6 | `reload(sys)` | `from importlib import reload` |
| main.py | 7 | `sys.setdefaultencoding('utf-8')` | Remove (UTF-8 is default) |
| objc_dep.py | Throughout | `.iteritems()` (9x) | `.items()` |
| objc_dep.py | 154 | `.itervalues()` (1x) | `.values()` |
| objc_dep.py | 22 | `from sets import Set` | Use built-in `set` |
| objc_dep.py | 154 | `map()` returns list | Wrap in `list()` |
| objc_dep.py | 1 | `#!/usr/bin/python` | `#!/usr/bin/env python3` |

**COMPATIBILITY CHECKS NEEDED:**
- PyObjC 3.x+ for Python 3 support
- macOS framework bindings (Foundation, AppKit, Quartz)
- Subprocess calls and encoding handling
- File I/O operations

---

## 2. Environment Setup

### 2.1 Install Python 3

**Option A: Homebrew (Recommended)**
```bash
# Install Python 3
brew install python@3.11

# Verify installation
python3 --version
which python3
```

**Option B: Official Python.org Installer**
- Download from https://www.python.org/downloads/
- Install Python 3.11+ for macOS

### 2.2 Install PyObjC for Python 3

```bash
# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install PyObjC framework
pip3 install pyobjc

# Verify PyObjC installation
python3 -c "import objc; print(objc.__version__)"
python3 -c "from Foundation import NSObject; print('Foundation OK')"
python3 -c "from AppKit import NSApplication; print('AppKit OK')"
python3 -c "from Quartz import CGImageCreate; print('Quartz OK')"
```

### 2.3 Backup Current State

```bash
# Create backup branch
git checkout -b python2-backup
git push origin python2-backup

# Create migration branch
git checkout master
git checkout -b python3-migration
```

---

## 3. Code Migration Steps

### 3.1 Phase 1: main.py Updates

**File**: `/Users/erutan/Repos/ImageAlpha/main.py`

**Current Code (Lines 5-8):**
```python
import sys
reload(sys)
sys.setdefaultencoding('utf-8') # can't avoid default encoding
import os
```

**Updated Code:**
```python
import sys
import os
# Python 3 uses UTF-8 by default, no need to set encoding
```

**Changes:**
- ✅ Remove `reload(sys)`
- ✅ Remove `sys.setdefaultencoding('utf-8')`
- ✅ Add comment explaining removal

### 3.2 Phase 2: objc_dep.py Updates

**File**: `/Users/erutan/Repos/ImageAlpha/Sparkle/objc_dep/objc_dep.py`

**Change 1: Shebang (Line 1)**
```python
# Before
#!/usr/bin/python

# After
#!/usr/bin/env python3
```

**Change 2: Import Statement (Line 22)**
```python
# Before
from sets import Set

# After
# 'sets' module removed in Python 3, use built-in set
# (No import needed)
```

**Change 3: Replace `Set()` with `set()` (Throughout)**
```python
# Find all occurrences of Set() and replace with set()
# Approximately 15 occurrences
```

**Change 4: Dictionary Iteration Methods**

Replace `.iteritems()` with `.items()` (9 occurrences):
```python
# Before
for k, v in some_dict.iteritems():

# After
for k, v in some_dict.items():
```

Replace `.itervalues()` with `.values()` (1 occurrence):
```python
# Before (Line 154)
lengths = map(lambda x:len(x), d.itervalues())

# After
lengths = list(map(lambda x: len(x), d.values()))
```

**Note**: Wrap `map()` in `list()` because Python 3 map returns iterator.

### 3.3 Phase 3: Automated Migration Check

Run Python's 2to3 tool to identify any missed issues:

```bash
# Dry run - see what would change
2to3 -n ./*.py

# Generate diff for review
2to3 -d ./*.py > migration_diff.txt

# Review the diff before applying
cat migration_diff.txt
```

**Do NOT auto-apply 2to3** - review changes manually to ensure PyObjC compatibility.

### 3.4 Phase 4: Verify All Python Files

Run these checks on all 9 Python files:

```bash
# Check for Python 2 patterns
grep -r "\.iteritems()" *.py
grep -r "\.itervalues()" *.py
grep -r "\.iterkeys()" *.py
grep -r "from sets import" *.py
grep -r "reload(sys)" *.py
grep -r "setdefaultencoding" *.py
grep -r "print " *.py  # Print statements (without parentheses)
grep -r "except.*," *.py  # Old-style exception syntax
```

All should return no results after migration.

---

## 4. Dependency Updates

### 4.1 Create requirements.txt

Create a new file to document Python dependencies:

**File**: `/Users/erutan/Repos/ImageAlpha/requirements.txt`
```
pyobjc>=9.0
pyobjc-framework-Cocoa>=9.0
pyobjc-framework-Quartz>=9.0
```

### 4.2 Verify PyObjC Compatibility

Test critical PyObjC features:

```bash
# Create test script
cat > test_pyobjc.py << 'EOF'
#!/usr/bin/env python3
import sys
print(f"Python version: {sys.version}")

from Foundation import NSObject, NSLog
from AppKit import NSApplication, NSImage, NSView
from Quartz import CGImageCreate, CGBitmapContextCreate
import objc

print("✓ Foundation imported")
print("✓ AppKit imported")
print("✓ Quartz imported")
print(f"✓ PyObjC version: {objc.__version__}")

# Test decorator (used throughout codebase)
class TestClass(NSObject):
    @objc.IBAction
    def testAction_(self, sender):
        pass

print("✓ objc.IBAction decorator works")
print("\nAll PyObjC imports successful!")
EOF

python3 test_pyobjc.py
```

### 4.3 External Tool Verification

Verify external command-line tools still work:

```bash
# Check pngquant
pngquant --version

# Check if pngnq exists
which pngnq || echo "pngnq not found - may need installation"

# Check posterizer (from submodule)
ls -la mediancut-posterizer/
```

---

## 5. Build System Updates

### 5.1 Update Xcode Project

**File**: `ImageAlpha.xcodeproj/project.pbxproj`

**Changes needed:**
1. Update Python framework search path
2. Point to Homebrew Python 3 framework
3. Update build settings

**Before** (Approximate):
```
FRAMEWORK_SEARCH_PATHS = /System/Library/Frameworks/Python.framework
```

**After**:
```
FRAMEWORK_SEARCH_PATHS = /opt/homebrew/Frameworks/Python.framework
# Or: /usr/local/Cellar/python@3.11/3.11.x/Frameworks/Python.framework
```

### 5.2 Update Build Configuration

**Files**:
- `debug.xcconfig`
- `release.xcconfig`

Update any Python version references or paths.

### 5.3 Update Info.plist

**File**: `ImageAlpha-Info.plist`

Verify or update:
```xml
<key>LSMinimumSystemVersion</key>
<string>10.8</string>  <!-- May need to increase for Python 3 -->

<key>CFBundleVersion</key>
<string>2.0.0</string>  <!-- Increment version -->
```

### 5.4 Update main.m (Objective-C Entry Point)

**File**: Check if `main.m` needs Python 3 path updates

```objective-c
// Verify Python initialization code
// May need to update Python framework path
```

---

## 6. Testing Plan

### 6.1 Unit Testing Strategy

**Create basic test suite:**

```bash
# Create tests directory
mkdir -p tests

# Create test runner
cat > tests/test_basic.py << 'EOF'
#!/usr/bin/env python3
"""Basic syntax and import tests"""

def test_imports():
    """Test all critical imports"""
    import main
    import ImageAlphaDocument
    import IAImage
    import IAImageView
    import IAImageViewInteractive
    import IASlider
    import IACollectionItem
    import IABackgroundRenderer
    print("✓ All imports successful")

def test_pyobjc():
    """Test PyObjC integration"""
    from Foundation import NSObject
    from AppKit import NSApplication
    from Quartz import CGImageCreate
    print("✓ PyObjC frameworks accessible")

if __name__ == '__main__':
    test_imports()
    test_pyobjc()
    print("\n✓ All basic tests passed!")
EOF

python3 tests/test_basic.py
```

### 6.2 Functional Testing Checklist

**Build and Launch:**
- [ ] Application builds without errors in Xcode
- [ ] Application launches and shows main window
- [ ] No Python runtime errors in Console.app

**Core Functionality:**
- [ ] Open PNG file via File > Open
- [ ] Open PNG file via drag-and-drop
- [ ] Preview image displays correctly
- [ ] Quality slider adjusts preview
- [ ] Colors slider adjusts preview
- [ ] Dithering options work (None, Floyd-Steinberg, etc.)
- [ ] Save optimized PNG
- [ ] Saved file is valid and optimized

**Advanced Features:**
- [ ] Batch processing multiple files
- [ ] Compare original vs optimized (split view)
- [ ] Collection view displays thumbnails
- [ ] Background rendering doesn't block UI
- [ ] Progress indicators work correctly
- [ ] Sparkle auto-update framework works

**Integration:**
- [ ] pngquant subprocess executes correctly
- [ ] posterizer subprocess executes correctly
- [ ] File encoding/decoding works (UTF-8)
- [ ] Temporary file handling works
- [ ] Error dialogs display properly

**Performance:**
- [ ] No memory leaks (run Instruments)
- [ ] Responsive UI during processing
- [ ] Large files (>10MB) process correctly

### 6.3 Regression Testing

Test on multiple macOS versions:
- [ ] macOS 10.15 Catalina (if still supporting)
- [ ] macOS 11 Big Sur
- [ ] macOS 12 Monterey
- [ ] macOS 13 Ventura
- [ ] macOS 14 Sonoma
- [ ] macOS 15 Sequoia (current)

### 6.4 Error Handling

Test error scenarios:
- [ ] Invalid PNG file
- [ ] Corrupted file
- [ ] No write permissions
- [ ] Disk full
- [ ] Missing pngquant binary
- [ ] Cancel during processing

---

## 7. Rollback Strategy

### 7.1 Git-Based Rollback

```bash
# If migration fails, rollback to Python 2
git checkout python2-backup

# Or reset migration branch
git checkout python3-migration
git reset --hard origin/master
```

### 7.2 Backup Checklist

Before migration:
- [x] Create `python2-backup` branch
- [ ] Tag current master: `git tag python2-final`
- [ ] Archive built .app bundle
- [ ] Document current build environment
- [ ] Save Xcode project settings

### 7.3 Incremental Commits

Commit after each phase:
```bash
git commit -m "Phase 1: Update main.py for Python 3"
git commit -m "Phase 2: Update objc_dep.py for Python 3"
git commit -m "Phase 3: Update Xcode build settings"
git commit -m "Phase 4: Testing and validation"
```

---

## 8. Post-Migration Tasks

### 8.1 Documentation Updates

**Update README.md:**
- Update Python version requirement (Python 3.9+)
- Update installation instructions
- Update build instructions
- Add PyObjC installation steps

**Create CHANGELOG.md:**
```markdown
## Version 2.0.0 (2025-XX-XX)

### Major Changes
- **Python 3 Migration**: Migrated from Python 2 to Python 3.9+
- Updated PyObjC to version 9.0+
- Modernized all deprecated syntax

### Requirements
- macOS 10.15+ (updated from 10.8+)
- Python 3.9 or later
- PyObjC 9.0+

### Breaking Changes
- No longer compatible with system Python 2
- Requires Homebrew Python 3 or official Python.org installation
```

### 8.2 Continuous Integration

Set up GitHub Actions for automated testing:

**File**: `.github/workflows/build.yml`
```yaml
name: Build and Test

on: [push, pull_request]

jobs:
  build:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python3 tests/test_basic.py
      - name: Build with Xcode
        run: |
          xcodebuild -project ImageAlpha.xcodeproj -scheme ImageAlpha -configuration Release
```

### 8.3 Release Preparation

- [ ] Update version number in Info.plist
- [ ] Update copyright year
- [ ] Build release binary
- [ ] Code sign application
- [ ] Notarize with Apple
- [ ] Create DMG installer
- [ ] Update website/download links
- [ ] Write release notes

### 8.4 Community Communication

- [ ] Announce Python 3 migration in README
- [ ] Create GitHub release with changelog
- [ ] Close related issues (if any about Python 2)
- [ ] Update any documentation/wiki

---

## 9. Timeline

### Week 1: Preparation and Code Migration

**Day 1-2: Environment Setup**
- Install Python 3 and PyObjC
- Verify all dependencies
- Create backup branches
- Run initial compatibility checks

**Day 3-4: Code Migration**
- Update main.py
- Update objc_dep.py
- Update all other Python files
- Run automated checks

**Day 5: Build System**
- Update Xcode project
- Update build configurations
- Test compilation

### Week 2: Testing and Release

**Day 6-8: Testing**
- Run unit tests
- Functional testing checklist
- Test on multiple macOS versions
- Fix any discovered issues

**Day 9: Documentation**
- Update README
- Write CHANGELOG
- Update build instructions

**Day 10: Release**
- Final build and testing
- Create release
- Deploy updates

---

## Risk Assessment

### High Risk Items

1. **PyObjC Compatibility**
   - **Risk**: PyObjC 3.x may have breaking changes
   - **Mitigation**: Extensive testing, fallback to compatible version
   - **Likelihood**: Low

2. **macOS Framework Bindings**
   - **Risk**: Framework APIs may have changed
   - **Mitigation**: Test on multiple macOS versions
   - **Likelihood**: Medium

3. **Xcode Build Issues**
   - **Risk**: Xcode project may not find Python 3 framework
   - **Mitigation**: Clear documentation of framework paths
   - **Likelihood**: Medium

### Medium Risk Items

1. **External Tool Integration**
   - **Risk**: Subprocess calls may behave differently
   - **Mitigation**: Test pngquant/posterizer integration thoroughly
   - **Likelihood**: Low

2. **File Encoding**
   - **Risk**: UTF-8 default may cause issues with non-ASCII filenames
   - **Mitigation**: Test with international characters
   - **Likelihood**: Low

### Low Risk Items

1. **Performance Regression**
   - **Risk**: Python 3 may be slower
   - **Mitigation**: Benchmark before/after
   - **Likelihood**: Very Low (Python 3 is typically faster)

---

## Success Criteria

Migration is considered successful when:

✅ All Python code runs on Python 3.9+
✅ Application builds without errors
✅ Application launches and runs without crashes
✅ All core functionality works (open, optimize, save)
✅ All UI controls work correctly
✅ No regression in image quality or file size
✅ Tests pass on macOS 12+
✅ Documentation is updated
✅ Release build is created and notarized

---

## Appendix A: File-by-File Changes

### main.py
- Remove `reload(sys)`
- Remove `sys.setdefaultencoding()`

### objc_dep.py
- Update shebang to `#!/usr/bin/env python3`
- Replace `from sets import Set` with built-in `set`
- Replace all `Set()` calls with `set()`
- Replace `.iteritems()` with `.items()` (9x)
- Replace `.itervalues()` with `.values()` (1x)
- Wrap `map()` in `list()` where needed

### ImageAlphaDocument.py
- Review for Python 2 patterns (none expected)

### IAImage.py
- Review for Python 2 patterns (none expected)

### IAImageView.py
- Review for Python 2 patterns (none expected)

### IAImageViewInteractive.py
- Review for Python 2 patterns (none expected)

### IASlider.py
- Review for Python 2 patterns (none expected)

### IACollectionItem.py
- Review for Python 2 patterns (none expected)

### IABackgroundRenderer.py
- Review for Python 2 patterns (none expected)

---

## Appendix B: Resources

**Python 3 Migration Guides:**
- https://docs.python.org/3/howto/pyporting.html
- https://python-future.org/compatible_idioms.html

**PyObjC Documentation:**
- https://pyobjc.readthedocs.io/
- https://github.com/ronaldoussoren/pyobjc

**macOS Development:**
- https://developer.apple.com/documentation/appkit
- https://developer.apple.com/documentation/foundation

**Tools:**
- 2to3: Automated Python 2 to 3 converter
- modernize: Python modernization tool
- futurize: Python 2/3 compatibility tool

---

## Appendix C: Contact and Support

**Questions or Issues:**
- GitHub Issues: https://github.com/pornel/ImageAlpha/issues
- Original Author: Kornel Lesiński

**Testing Help:**
- Request beta testers from existing user base
- Test on variety of macOS versions and hardware

---

**End of Migration Plan**

*This plan should be reviewed and updated as migration progresses.*
