#
#  IAPreferencesController.py
#

import objc
from objc import *
from Foundation import *
from AppKit import *

# Toolbar item identifiers
TOOLBAR_GENERAL = "GeneralToolbarItem"
TOOLBAR_OXIPNG = "OxipngToolbarItem"
TOOLBAR_ZOPFLIPNG = "ZopflipngToolbarItem"


class IAPreferencesController(NSWindowController):

    _sharedInstance = None

    # IBOutlets for the three tab views
    generalView = objc.IBOutlet()
    oxipngView = objc.IBOutlet()
    zopflipngView = objc.IBOutlet()

    # IBOutlets for dither radio buttons
    ditherDefaultButton = objc.IBOutlet()
    ditherOnButton = objc.IBOutlet()
    ditherOffButton = objc.IBOutlet()

    _currentView = None
    _toolbar = None

    @classmethod
    def sharedInstance(cls):
        if cls._sharedInstance is None:
            cls._sharedInstance = cls.alloc().initWithWindowNibName_("Preferences")
        return cls._sharedInstance

    def windowDidLoad(self):
        super(IAPreferencesController, self).windowDidLoad()
        self._setupToolbar()
        # Select General tab by default
        self._switchToView_(self.generalView, TOOLBAR_GENERAL)
        # Initialize dither radio button states
        self._updateDitherRadioButtons()

    @objc.python_method
    def _setupToolbar(self):
        toolbar = NSToolbar.alloc().initWithIdentifier_("PreferencesToolbar")
        toolbar.setDelegate_(self)
        toolbar.setAllowsUserCustomization_(False)
        toolbar.setDisplayMode_(NSToolbarDisplayModeIconAndLabel)
        toolbar.setSelectedItemIdentifier_(TOOLBAR_GENERAL)
        toolbar.setCenteredItemIdentifiers_(NSSet.setWithArray_([TOOLBAR_GENERAL, TOOLBAR_OXIPNG, TOOLBAR_ZOPFLIPNG]))
        self.window().setToolbar_(toolbar)
        # Use modern preferences window style (title shows tab name, centered toolbar)
        self.window().setToolbarStyle_(2)  # NSWindowToolbarStylePreference
        self._toolbar = toolbar

    # NSToolbar delegate methods
    def toolbarAllowedItemIdentifiers_(self, toolbar):
        return [TOOLBAR_GENERAL, TOOLBAR_OXIPNG, TOOLBAR_ZOPFLIPNG]

    def toolbarDefaultItemIdentifiers_(self, toolbar):
        return [TOOLBAR_GENERAL, TOOLBAR_OXIPNG, TOOLBAR_ZOPFLIPNG]

    def toolbarSelectableItemIdentifiers_(self, toolbar):
        return [TOOLBAR_GENERAL, TOOLBAR_OXIPNG, TOOLBAR_ZOPFLIPNG]

    def toolbar_itemForItemIdentifier_willBeInsertedIntoToolbar_(self, toolbar, identifier, flag):
        item = NSToolbarItem.alloc().initWithItemIdentifier_(identifier)

        if identifier == TOOLBAR_GENERAL:
            item.setLabel_("General")
            # Use SF Symbol gear icon
            gearImage = NSImage.imageWithSystemSymbolName_accessibilityDescription_("gearshape", "General")
            item.setImage_(gearImage)
            item.setTarget_(self)
            item.setAction_(self.switchToGeneralTab_)
        elif identifier == TOOLBAR_OXIPNG:
            item.setLabel_("oxipng")
            # Use SF Symbol compression icon
            compressImage = NSImage.imageWithSystemSymbolName_accessibilityDescription_("arrow.down.right.and.arrow.up.left", "Compression")
            item.setImage_(compressImage)
            item.setTarget_(self)
            item.setAction_(self.switchToOxipngTab_)
        elif identifier == TOOLBAR_ZOPFLIPNG:
            item.setLabel_("zopflipng")
            # Use SF Symbol compression icon
            compressImage = NSImage.imageWithSystemSymbolName_accessibilityDescription_("arrow.down.right.and.arrow.up.left", "Compression")
            item.setImage_(compressImage)
            item.setTarget_(self)
            item.setAction_(self.switchToZopflipngTab_)

        return item

    @objc.IBAction
    def setDitherDefault_(self, sender):
        NSUserDefaults.standardUserDefaults().removeObjectForKey_("dithered")
        self._updateDitherRadioButtons()

    @objc.IBAction
    def setDitherOn_(self, sender):
        NSUserDefaults.standardUserDefaults().setBool_forKey_(True, "dithered")
        self._updateDitherRadioButtons()

    @objc.IBAction
    def setDitherOff_(self, sender):
        NSUserDefaults.standardUserDefaults().setBool_forKey_(False, "dithered")
        self._updateDitherRadioButtons()

    @objc.python_method
    def _updateDitherRadioButtons(self):
        """Update radio button states based on current dithered preference."""
        if self.ditherDefaultButton is None:
            return

        defaults = NSUserDefaults.standardUserDefaults()
        stored = defaults.objectForKey_("dithered")

        # Determine which button should be selected
        # stored is None = default, True = on, False = off
        if stored is None:
            tag = -1  # default
        elif hasattr(stored, "boolValue"):
            tag = 1 if stored.boolValue() else 0
        else:
            tag = 1 if stored else 0

        self.ditherDefaultButton.setState_(NSControlStateValueOn if tag == -1 else NSControlStateValueOff)
        self.ditherOnButton.setState_(NSControlStateValueOn if tag == 1 else NSControlStateValueOff)
        self.ditherOffButton.setState_(NSControlStateValueOn if tag == 0 else NSControlStateValueOff)

    @objc.IBAction
    def switchToGeneralTab_(self, sender):
        self._switchToView_(self.generalView, TOOLBAR_GENERAL)

    @objc.IBAction
    def switchToOxipngTab_(self, sender):
        self._switchToView_(self.oxipngView, TOOLBAR_OXIPNG)

    @objc.IBAction
    def switchToZopflipngTab_(self, sender):
        self._switchToView_(self.zopflipngView, TOOLBAR_ZOPFLIPNG)

    @objc.python_method
    def _switchToView_(self, newView, identifier):
        if newView is None:
            return

        window = self.window()

        # Calculate new window frame
        newFrame = window.frameRectForContentRect_(newView.frame())
        currentFrame = window.frame()

        # Keep top-left corner fixed
        newFrame.origin.x = currentFrame.origin.x
        newFrame.origin.y = currentFrame.origin.y + currentFrame.size.height - newFrame.size.height

        # Remove current view if any
        if self._currentView is not None:
            self._currentView.removeFromSuperview()

        # Resize window and add new view
        window.setFrame_display_animate_(newFrame, True, True)
        window.contentView().addSubview_(newView)
        newView.setFrameOrigin_(NSMakePoint(0, 0))

        self._currentView = newView

        # Update toolbar selection
        if self._toolbar is not None:
            self._toolbar.setSelectedItemIdentifier_(identifier)

        # Update window title to show current tab name
        tabNames = {
            TOOLBAR_GENERAL: "General",
            TOOLBAR_OXIPNG: "oxipng",
            TOOLBAR_ZOPFLIPNG: "zopflipng"
        }
        window.setTitle_(tabNames.get(identifier, "Preferences"))


# Action that can be called from First Responder
@objc.IBAction
def openPreferences_(self, sender):
    controller = IAPreferencesController.sharedInstance()
    controller.showWindow_(sender)
    controller.window().makeKeyAndOrderFront_(sender)

# Add the action to NSApplication
NSApplication.openPreferences_ = openPreferences_
