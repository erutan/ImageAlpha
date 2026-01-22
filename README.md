# ImageAlpha

ImageAlpha is a Mac OS X GUI for [pngquant](http://pngquant.org), with optional lossless optimization via [oxipng](https://github.com/oxipng/oxipng) and extra (very slow) compression via [zopflipng](https://github.com/google/zopfli).

ImageAlpha is written in Python and Cocoa (PyObjC).

![Screenshot](https://pngmini.com/screenshot-1.3.png)

## Testing

Run tests via Xcode with **Cmd+U**, or from the command line:

```bash
./Frameworks/Python.framework/Versions/3.13/bin/python3 test_compression_settings.py
```

Tests include:
- **Argument generation** (37 tests) - verifies oxipng/zopflipng command-line arguments match preferences
- **Preference persistence** (4 tests) - verifies NSUserDefaults read/write
- **Default settings** (8 tests) - verifies new images get correct default lossless mode/dithering
- **Integration tests** (6 tests) - runs actual oxipng/zopflipng/pngquant on test image

## Language Support
* 中文简体 (Chinese Simplified) - [Pluwen](https://twitter.com/pluwen)
