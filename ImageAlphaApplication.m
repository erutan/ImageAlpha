

#import "ImageAlphaApplication.h"

@implementation ImageAlphaApplication

@synthesize imageOptimPath, ditheredMenu;

+(void)initialize {
    if (self == [ImageAlphaApplication class]) {
        // Register default values for user preferences
        NSDictionary *defaults = @{
            // General settings
            @"defaultLosslessMode": @1,  // 0=none, 1=oxipng, 2=zopflipng
            @"rememberColorCount": @NO,
            @"lastColorCount": @256,
            @"Optimize": @NO,

            // oxipng settings
            @"oxipng.optimizationLevel": @4,
            @"oxipng.maxOptimization": @NO,
            @"oxipng.stripMetadata": @1,  // 0=none, 1=safe, 2=all
            @"oxipng.alphaOptimization": @NO,
            @"oxipng.interlace": @0,  // 0=keep, 1=on, 2=off
            @"oxipng.threads": @0,  // 0=auto
            @"oxipng.timeout": @0,  // 0=disabled

            // zopflipng settings
            @"zopflipng.iterations": @15,
            @"zopflipng.maxCompression": @NO,
            @"zopflipng.quickMode": @NO,
            @"zopflipng.keepChunks": @"",
        };
        [[NSUserDefaults standardUserDefaults] registerDefaults:defaults];
    }
}

-(void)applicationDidFinishLaunching:(NSApplication*)sender {
    NSURL *appURL = [[NSWorkspace sharedWorkspace] URLForApplicationWithBundleIdentifier:@"net.pornel.imageoptim"];
    self.imageOptimPath = appURL.path;

    id dithered = [[NSUserDefaults standardUserDefaults] objectForKey:@"dithered"];
    int tag = dithered != nil ? [dithered boolValue] : -1;
    for (NSMenuItem *item in self.ditheredMenu.itemArray) {
        [item setState:item.tag == tag ? NSControlStateValueOn : NSControlStateValueOff];
    }
}

- (IBAction)checkForUpdates:(id)sender {
    [[NSWorkspace sharedWorkspace] openURL:[NSURL URLWithString:@"https://github.com/erutan/ImageAlpha/releases"]];
}

@end
