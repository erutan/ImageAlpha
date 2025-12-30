#
#  main.py

# Python 3 uses UTF-8 by default; no encoding override needed.

#import modules required by application
import objc
import Foundation
import AppKit

objc.setVerbose(0)

from PyObjCTools import AppHelper

# import modules containing classes required to start application and load MainMenu.nib

import ImageAlphaDocument
import IASlider
import IACollectionItem
import IAImageViewInteractive
import IABackgroundRenderer
import IAImageView
import IAImage

# pass control to AppKit
AppHelper.runEventLoop()
