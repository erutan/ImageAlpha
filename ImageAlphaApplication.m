

#import "ImageAlphaApplication.h"

@implementation ImageAlphaApplication

@synthesize imageOptimPath, ditheredMenu;

-(void)applicationDidFinishLaunching:(NSApplication*)sender {
    NSURL *appURL = [[NSWorkspace sharedWorkspace] URLForApplicationWithBundleIdentifier:@"net.pornel.imageoptim"];
    self.imageOptimPath = appURL.path;

    id dithered = [[NSUserDefaults standardUserDefaults] objectForKey:@"dithered"];
    int tag = dithered != nil ? [dithered boolValue] : -1;
    for (NSMenuItem *item in self.ditheredMenu.itemArray) {
        [item setState:item.tag == tag ? NSControlStateValueOn : NSControlStateValueOff];
    }
}

@end
