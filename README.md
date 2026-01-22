# ImageAlpha

ImageAlpha is a Mac OS X GUI for [pngquant](http://pngquant.org), with optional lossless optimization via [oxipng](https://github.com/oxipng/oxipng) and extra (very slow) compression via [zopflipng](https://github.com/google/zopfli).

ImageAlpha is written in Python and Cocoa (PyObjC).

![Screenshot](https://pngmini.com/screenshot-1.3.png)

## Testing

Run the compression settings tests:

```bash
./Frameworks/Python.framework/Versions/3.13/bin/python3 test_compression_settings.py
```

This tests the argument generation for oxipng and zopflipng based on preference settings.

## Language Support
* 中文简体 (Chinese Simplified) - [Pluwen](https://twitter.com/pluwen)
