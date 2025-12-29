# ImageAlpha Python 3 Migration Plan (Codex)

## Summary
ImageAlpha is a Python + PyObjC macOS app that embeds the system Python 2 runtime. Moving to Python 3 is feasible, but the biggest changes are in the embedding/runtime and updating bundled native tools and Sparkle. Decision: use an embedded Python approach (bundle Python.framework + PyObjC), sourced from the python.org macOS universal2 installer.

## Work Needed (Findings)

### 1) Embedded Python 2 runtime
- The app hard-codes `/usr/bin/python` and links `System/Library/Frameworks/Python.framework`, which is removed on modern macOS.
- `main.m` uses Python 2 C-API entry points and argv handling.

### 2) Python source compatibility
- `main.py` uses `reload(sys)` and `sys.setdefaultencoding(...)` which do not exist in Python 3.
- `IAImage.py` uses `NSUserDefaults.standardUserDefaults().get(...)` which is not a valid PyObjC call pattern in Python 3, and the file has mixed tab indentation.
- There may be other PyObjC API changes for constants or selectors that need small adjustments.

### 3) PyObjC runtime compatibility
- The app relies on PyObjC. Python 3.14 support may lag; Python 3.12/3.13 may be the practical target if PyObjC is not yet compatible.
- Embedded approach chosen; bundle the python.org macOS universal2 Python.framework.

### 4) Bundled native tools
- Projects reference external source trees that are missing in this repo: `pngquant`, `pngnq`, and `posterizer`.
- `libpng.xcodeproj` points to an external path (`../ImageOptim/libpng`).
- These tools must be re-vendored or replaced with prebuilt binaries, and updated for arm64/x86_64.

### 5) Sparkle (update framework)
- The repo contains Sparkle 1 (DSA key + legacy feed). Modern macOS requires Sparkle 2 for notarization and secure updates.
- Migrate to Sparkle 2 with EdDSA signing and a modern appcast format.

### 6) macOS build settings
- Deployment target is 10.7/10.8 and `LSArchitecturePriority` is x86_64 only.
- Update to current deployment target and add arm64 support, modernize build settings, and add hardened runtime/notarization.

## Plan

### Phase 0: Baseline and repo cleanup
1) Confirm which tool sources are expected to be in this repo (`pngquant`, `pngnq`, `posterizer`, `libpng`) and decide whether to vendor or fetch them as submodules.
2) Python 3 target version: 3.13 (PyObjC 12.1 classifiers include 3.13; requires Python >=3.10).
3) Embedded packaging chosen; use the python.org macOS universal2 Python.framework and vendor it into the app bundle.

### Phase 0 baseline notes (current repo state)
- `pngquant.xcodeproj` expects `pngquant/` sources that are not present.
- `pngnq.xcodeproj` expects `pngnq/src/` sources that are not present.
- `posterizer.xcodeproj` expects `posterizer/` sources; only `mediancut-posterizer/` exists.
- `libpng.xcodeproj` points outside the repo (`../ImageOptim/libpng`).
- `main.m` sets `PYTHONPATH` to a `PyObjC/` folder in app resources that is not present.

### Phase 1: Python 3 runtime + embedding
1) Update `main.m` to Python 3 embedding API (use `PyConfig` / `Py_InitializeFromConfig`, wide-char argv).
2) Update Xcode project to link the embedded Python 3 framework and set `PYTHONPATH` to the app’s resources.
3) Validate the app can start and run the PyObjC event loop with the embedded runtime.

### Phase 2: Python code port
1) Remove `reload(sys)` / `sys.setdefaultencoding` from `main.py`.
2) Replace deprecated PyObjC calls (e.g., `NSUserDefaults...get` -> `objectForKey_` or `boolForKey_` as appropriate).
3) Normalize indentation and fix any Python 3 syntax or API changes.
4) Run the app and confirm UI behavior (drag/drop, zoom, background selection, save/export).

### Phase 3: Native toolchain updates
1) Re-vendor or update `pngquant`, `pngnq`, `posterizer`, and `libpng` sources to current versions.
2) Update each Xcode project to build universal binaries (arm64 + x86_64).
3) Verify tools are embedded as auxiliary executables and invoked correctly from Python.

### Phase 4: Sparkle and app modernization
1) Migrate Sparkle to v2: update framework, appcast format, and signing.
2) Update `Info.plist` for modern macOS compatibility and document types if needed.
3) Add hardened runtime, entitlements, and notarization steps.

### Phase 5: Build + QA
1) Build the app on macOS 26.2 with the new Python runtime.
2) Test critical workflows: open file, adjust colors, save/export, ImageOptim integration.
3) Verify update checks via Sparkle 2 and sign/notarize.

## Risks / Open Questions
- PyObjC + Python 3.14 compatibility may not be available; may need to target 3.12/3.13.
- Missing tool sources must be recovered or replaced; otherwise functionality is incomplete.
- Sparkle 1 cannot be used for modern notarized releases.

## Suggested Immediate Next Steps
1) Decide on the Python 3 target (3.12/3.13 vs 3.14).
2) Decide how to source/bundle `pngquant`, `pngnq`, `posterizer`, and `libpng`.
