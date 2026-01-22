#
#  IAImage.py
import objc
from objc import *
from Foundation import *
from AppKit import *
from math import log
import os
import shutil
import threading
import uuid

class Quantizer(object):
    def qualityLabel(self):
        return "Colors"

    def supportsIeMode(self):
        return False

    def preferredDithering(self):
        return True

    def numberOfColorsToQuality(self, colors):
        return colors;

    def versionId(self, colors, dithering, ieMode):
        return "c%d:m%s:d%d%d" % (self.numberOfColorsToQuality(colors), self.__class__.__name__, dithering, ieMode)

class Pngquant(Quantizer):
    def supportsIeMode(self):
        return False

    def launchArguments(self, dither, colors, ieMode):
        args = []
        if not dither:
            args.append("--nofs")
        args.append("%d" % colors)
        args.append("-")
        return ("pngquant", args)

class Pngnq(Quantizer):
    def launchArguments(self, dither, colors, ieMode):
        return ("pngnq", ["-Q","f" if dither else "n","-n","%d" % colors, "-"])

class Posterizer(Quantizer):
    def qualityLabel(self):
        return "Quality"

    def preferredDithering(self):
        return False

    def numberOfColorsToQuality(self, c):
        return round(15 + (c * 240 / 255));

    def launchArguments(self, dither, colors, ieMode):
        args = ["%d" % self.numberOfColorsToQuality(colors)];
        if dither:
            args.insert(0,"-d")
        args.append("-")
        return ("posterizer",args);

class Blurizer(Quantizer):
    def qualityLabel(self):
        return "Quality"

    def preferredDithering(self):
        return True

    def versionId(self, colors, dithering, ieMode):
        return "blur%d" % self.numberOfColorsToQuality(colors)

    def numberOfColorsToQuality(self, c):
        return round(255 - 12 + 1.5*log(c, 2));

    def launchArguments(self, dither, colors, ieMode):
        args = ["-b", "%d" % self.numberOfColorsToQuality(colors)];
        args.append("-")
        return ("posterizer",args);


class IAImage(NSObject):
    _image = None
    _imageData = None

    path = None
    _sourceFileSize = None

    versions = None

    _numberOfColors = 256;

    _quantizationMethod = 0; # 0 = pngquant
    _quantizationMethods = [
        Pngquant(),
    ]
    _dithering = YES
    _losslessMode = 1  # 0 = none, 1 = oxipng, 2 = zopflipng

    callbackWhenImageChanges = None

    def init(self):
        self = super(IAImage, self).init()
        self.versions = {};
        self.updateDithering()
        self.updateLosslessMode()
        return self

    def updateLosslessMode(self):
        """Set initial lossless mode from user defaults."""
        defaults = NSUserDefaults.standardUserDefaults()
        mode = defaults.integerForKey_("defaultLosslessMode")
        # 0=none, 1=oxipng, 2=zopflipng
        if mode in (0, 1, 2):
            self._losslessMode = mode

    def setCallbackWhenImageChanges_(self, documentToCallback):
        self.callbackWhenImageChanges = documentToCallback;
        self.update()

    def setImage_(self,image):
        self._image = image

    def image(self):
        return self._image

    def imageData(self):
        return self._imageData;

    def sourceFileSize(self):
        return self._sourceFileSize;

    def setPath_(self,path):
        self.path = path
        (attrs,error) = NSFileManager.defaultManager().attributesOfItemAtPath_error_(self.path,None);
        self._sourceFileSize = attrs.objectForKey_(NSFileSize) if attrs is not None and error is None else None;

    def ieMode(self):
        return self._losslessMode == 1

    def setIeMode_(self,val):
        if int(val) > 0:
            self._setLosslessMode(1)
        else:
            self._setLosslessMode(0)

    def losslessNone(self):
        return self._losslessMode == 0

    def setLosslessNone_(self,val):
        if int(val) > 0:
            self._setLosslessMode(0)

    def losslessOxipng(self):
        return self._losslessMode == 1

    def setLosslessOxipng_(self,val):
        if int(val) > 0:
            self._setLosslessMode(1)

    def losslessZopfli(self):
        return self._losslessMode == 2

    def setLosslessZopfli_(self,val):
        if int(val) > 0:
            self._setLosslessMode(2)

    def losslessMode(self):
        return self._losslessMode

    def setLosslessMode_(self,val):
        self._setLosslessMode(int(val))

    @objc.python_method
    def _setLosslessMode(self, mode):
        if self._losslessMode == mode:
            return
        self.willChangeValueForKey_("losslessNone")
        self.willChangeValueForKey_("losslessOxipng")
        self.willChangeValueForKey_("losslessZopfli")
        self._losslessMode = mode
        self.didChangeValueForKey_("losslessNone")
        self.didChangeValueForKey_("losslessOxipng")
        self.didChangeValueForKey_("losslessZopfli")
        self.update()

    def dithering(self):
        return self._dithering

    def setDithering_(self,val):
        self._dithering = int(val) > 0
        self.update()

    def updateDithering(self):
        defaults = NSUserDefaults.standardUserDefaults()
        stored = defaults.objectForKey_("dithered")
        if stored is None:
            value = self.quantizer().preferredDithering()
        elif hasattr(stored, "boolValue"):
            value = stored.boolValue()
        else:
            value = bool(stored)
        self.setDithering_(value)

    def numberOfColors(self):
        return self._numberOfColors

    def qualityLabel(self):
        return self.quantizer().qualityLabel()

    def setNumberOfColors_(self,num):
        self._numberOfColors = int(num)
        # Save color count if "remember" setting is enabled
        defaults = NSUserDefaults.standardUserDefaults()
        if defaults.boolForKey_("rememberColorCount"):
            defaults.setInteger_forKey_(self._numberOfColors, "lastColorCount")
        self.update()

    def quantizationMethod(self):
        return self._quantizationMethod

    def quantizer(self):
        if self._quantizationMethod >= len(self._quantizationMethods):
            self._quantizationMethod = 0
        return self._quantizationMethods[self._quantizationMethod]

    def setQuantizationMethod_(self,num):
        self.willChangeValueForKey_("qualityLabel");
        max_index = len(self._quantizationMethods) - 1
        self._quantizationMethod = max(0, min(int(num), max_index))
        self.didChangeValueForKey_("qualityLabel");

        self.updateDithering()
        self.update()

    def isBusy(self):
        if self.path is None: return False
        id = self.currentVersionId()
        if id not in self.versions: return False # not sure about this
        return not self.versions[id].isDone;

    def update(self):
        if self.path:
            id = self.currentVersionId()

            if self.numberOfColors() > 256:
                self._imageData = NSData.dataWithContentsOfFile_(self.path);
                self.setImage_(NSImage.alloc().initByReferencingFile_(self.path));

                if self.callbackWhenImageChanges is not None: self.callbackWhenImageChanges.imageChanged();

            elif id not in self.versions:
                self.versions[id] = IAImageVersion.alloc().init()
                self.versions[id].generateFromPath_method_dither_lossless_colors_callback_(self.path, self.quantizer(), self.dithering(), self.losslessMode(), self.numberOfColors(), self)

                if self.callbackWhenImageChanges is not None: self.callbackWhenImageChanges.updateProgressbar();

            elif self.versions[id].isDone:
                self._imageData = self.versions[id].imageData
                self.setImage_(NSImage.alloc().initWithData_(self._imageData))

                if self.callbackWhenImageChanges is not None: self.callbackWhenImageChanges.imageChanged();

    def currentVersionId(self):
        base_id = self.quantizer().versionId(self.numberOfColors(), self.dithering(), self.ieMode())
        return "%s:l%d" % (base_id, self.losslessMode())

    def destroy(self):
        self.callbackWhenImageChanges = None
        for id in self.versions:
            self.versions[id].destroy()
        self.versions = {}


class IAImageVersion(NSObject):
    imageData = None
    isDone = False

    task = None
    outputPipe = None
    callbackWhenFinished = None
    losslessMode = 0

    def generateFromPath_method_dither_lossless_colors_callback_(self,path,quantizer,dither,losslessMode,colors,callbackWhenFinished):

        self.isDone = False
        self.callbackWhenFinished = callbackWhenFinished
        self.losslessMode = int(losslessMode)

        (executable, args) = quantizer.launchArguments(dither, colors, 0)

        task = NSTask.alloc().init()
        self.task = task

        exePath = self._findExecutable(executable)
        if not exePath:
            NSLog("Missing helper executable: %s" % executable)
            self.isDone = True
            self.imageData = NSData.dataWithContentsOfFile_(path)
            if self.callbackWhenFinished is not None:
                self.callbackWhenFinished.update()
            return None
        task.setLaunchPath_(exePath)
        task.setCurrentDirectoryPath_(os.path.dirname(str(exePath)))
        task.setArguments_(args);

        # pngout works best via standard input/output
        file = NSFileHandle.fileHandleForReadingAtPath_(path);
        task.setStandardInput_(file);

        # get output via pipe
        # use pipe's file handle to construct NSData object asynchronously
        outputPipe = NSPipe.pipe();
        self.outputPipe = outputPipe
        task.setStandardOutput_(outputPipe);

        # pipe *must* be read, otheriwse task will block waiting for I/O
        handle = outputPipe.fileHandleForReading();
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, self.onHandleReadToEndOfFile_, NSFileHandleReadToEndOfFileCompletionNotification, handle);
        handle.readToEndOfFileInBackgroundAndNotify()

        task.launch();
        return task;

    @objc.python_method
    def _findExecutable(self, executable):
        bundle = NSBundle.mainBundle()
        exePath = bundle.pathForAuxiliaryExecutable_(executable)
        if exePath:
            return exePath

        if bundle.resourcePath() is not None:
            resourcePath = bundle.resourcePath().stringByAppendingPathComponent_(executable)
            if NSFileManager.defaultManager().isExecutableFileAtPath_(resourcePath):
                return resourcePath

        path = shutil.which(executable)
        if path:
            return path

        for prefix in ("/opt/homebrew/bin", "/usr/local/bin"):
            candidate = os.path.join(prefix, executable)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate

        return None

    def onHandleReadToEndOfFile_(self,notification):
        data = notification.userInfo().objectForKey_(NSFileHandleNotificationDataItem)
        if data is None:
            self.isDone = True
            if self.callbackWhenFinished is not None:
                self.callbackWhenFinished.update()
            return

        if self.losslessMode != 0:
            self._startOptimization_(data)
            return

        self.isDone = True
        self.imageData = data
        if self.callbackWhenFinished is not None:
            self.callbackWhenFinished.update()

    @objc.python_method
    def _startOptimization_(self, data):
        thread = threading.Thread(target=self._runOptimization_, args=(data,))
        thread.daemon = True
        thread.start()

    @objc.python_method
    def _runOptimization_(self, data):
        optimized = self._optimizeData_(data)
        if optimized is None:
            optimized = data
        self.performSelectorOnMainThread_withObject_waitUntilDone_(self._finishOptimization_, optimized, False)

    def _finishOptimization_(self, data):
        self.isDone = True
        self.imageData = data
        if self.callbackWhenFinished is not None:
            self.callbackWhenFinished.update()

    @objc.python_method
    def _optimizeData_(self, data):
        temp_dir = str(NSTemporaryDirectory())
        base_name = "ImageAlpha-" + uuid.uuid4().hex
        input_path = os.path.join(temp_dir, base_name + ".png")
        output_path = os.path.join(temp_dir, base_name + "-zopf.png")
        input_size = int(data.length()) if data is not None else 0

        if not data.writeToFile_atomically_(input_path, True):
            NSLog("Failed to write temp file for optimizers")
            return None

        optimized = None
        try:
            if self.losslessMode == 1:
                if self._runOxipng_(input_path):
                    optimized = NSData.dataWithContentsOfFile_(input_path)
                    self._logOptimizeResult_("oxipng", input_size, optimized)
                else:
                    return None
            elif self.losslessMode == 2:
                if self._runZopflipng_(input_path, output_path):
                    optimized = NSData.dataWithContentsOfFile_(output_path)
                    self._logOptimizeResult_("zopflipng", input_size, optimized)
                else:
                    return None
            if optimized is None:
                optimized = NSData.dataWithContentsOfFile_(input_path)
        finally:
            for path in (input_path, output_path):
                try:
                    os.unlink(path)
                except OSError:
                    pass

        return optimized

    @objc.python_method
    def _logOptimizeResult_(self, tool, input_size, optimized):
        if optimized is None:
            return
        output_size = int(optimized.length())
        NSLog("%s: %d -> %d bytes" % (tool, input_size, output_size))

    @objc.python_method
    def _getOxipngArguments_(self, input_path):
        """Build oxipng arguments from NSUserDefaults settings."""
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
            pass  # none - don't strip
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
            args.extend(["-i", "1"])  # on
        elif interlace == 2:
            args.extend(["-i", "0"])  # off
        # 0 = keep (don't specify)

        # Threads
        threads = defaults.integerForKey_("oxipng.threads")
        if threads > 0:
            args.extend(["--threads", str(threads)])

        # Timeout
        timeout = defaults.integerForKey_("oxipng.timeout")
        if timeout > 0:
            args.extend(["--timeout", str(timeout)])

        # Quiet mode and input file
        args.append("-q")
        args.append(input_path)

        return args

    @objc.python_method
    def _runOxipng_(self, input_path):
        exePath = self._findExecutable("oxipng")
        if not exePath:
            NSLog("Missing helper executable: oxipng")
            return False

        args = self._getOxipngArguments_(input_path)
        NSLog("oxipng args: %s" % " ".join(args))

        task = NSTask.alloc().init()
        task.setLaunchPath_(exePath)
        task.setArguments_(args)
        task.launch()
        task.waitUntilExit()

        if task.terminationStatus() != 0:
            NSLog("oxipng failed with status %d" % task.terminationStatus())
            return False

        return True

    @objc.python_method
    def _getZopflipngArguments_(self, input_path, output_path):
        """Build zopflipng arguments from NSUserDefaults settings."""
        defaults = NSUserDefaults.standardUserDefaults()
        args = ["-y"]  # Always overwrite output

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
        if keep_chunks and len(keep_chunks.strip()) > 0:
            # Split by comma and add each chunk
            for chunk in str(keep_chunks).split(","):
                chunk = chunk.strip()
                if chunk:
                    args.extend(["--keepchunks=%s" % chunk])

        # Input and output files
        args.append(input_path)
        args.append(output_path)

        return args

    @objc.python_method
    def _runZopflipng_(self, input_path, output_path):
        exePath = self._findExecutable("zopflipng")
        if not exePath:
            NSLog("Missing helper executable: zopflipng")
            return False

        args = self._getZopflipngArguments_(input_path, output_path)
        NSLog("zopflipng args: %s" % " ".join(args))

        task = NSTask.alloc().init()
        task.setLaunchPath_(exePath)
        task.setArguments_(args)
        task.launch()
        task.waitUntilExit()

        if task.terminationStatus() != 0:
            NSLog("zopflipng failed with status %d" % task.terminationStatus())
            return False

        return True

    # FIXME: use dealloc and super()?
    def destroy(self):
        NSNotificationCenter.defaultCenter().removeObserver_(self);
        self.callbackWhenFinished = None
        if self.task:
            self.task.terminate();
            self.task = None
        if self.outputPipe:
            self.outputPipe.fileHandleForReading().closeFile()
            self.outputPipe = None
