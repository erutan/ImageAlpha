
#import <Cocoa/Cocoa.h>

@interface ImageAlphaApplication : NSObject
@property (retain) NSString *imageOptimPath;
@property (retain) IBOutlet NSMenu *ditheredMenu;
- (IBAction)checkForUpdates:(id)sender;
@end
