//
//  main.m
//  ImageAlpha

#import <Python/Python.h>
#import <Cocoa/Cocoa.h>

static void ShowPythonErrorAlert(NSString *message)
{
    NSAlert *alert = [[NSAlert alloc] init];
    alert.messageText = @"Unable to start ImageAlpha";
    alert.informativeText = message;
    [alert addButtonWithTitle:@"Abort"];
    [alert runModal];
    [alert release];
}

int main(int argc, char *argv[])
{
    @autoreleasepool {
        NSBundle *mainBundle = [NSBundle mainBundle];
        NSString *frameworksPath = [mainBundle privateFrameworksPath];
        NSString *pythonHome = nil;

        if (frameworksPath) {
            pythonHome = [[frameworksPath stringByAppendingPathComponent:@"Python.framework"]
                          stringByAppendingPathComponent:@"Versions/Current"];
        }

        if (pythonHome == nil || ![[NSFileManager defaultManager] fileExistsAtPath:pythonHome]) {
            ShowPythonErrorAlert(@"Bundled Python.framework not found.");
            return -1;
        }

        NSArray *possibleMainExtensions = [NSArray arrayWithObjects: @"py", @"pyc", nil];
        NSString *mainFilePath = nil;

        for (NSString *possibleMainExtension in possibleMainExtensions) {
            mainFilePath = [mainBundle pathForResource:@"main" ofType:possibleMainExtension];
            if (mainFilePath != nil) break;
        }

        if (mainFilePath == nil) {
            ShowPythonErrorAlert(@"main.py not found in app resources.");
            return -1;
        }

        PyStatus status;
        PyConfig config;
        PyConfig_InitPythonConfig(&config);
        config.isolated = 1;

        status = PyConfig_SetBytesString(&config, &config.home, [pythonHome fileSystemRepresentation]);
        if (PyStatus_Exception(status)) goto python_error;

        status = PyConfig_SetBytesString(&config, &config.run_filename, [mainFilePath fileSystemRepresentation]);
        if (PyStatus_Exception(status)) goto python_error;

        status = PyConfig_SetBytesArgv(&config, argc, argv);
        if (PyStatus_Exception(status)) goto python_error;

        status = Py_InitializeFromConfig(&config);
        if (PyStatus_Exception(status)) goto python_error;

        PyConfig_Clear(&config);
        return Py_RunMain();

python_error:
        PyConfig_Clear(&config);
        ShowPythonErrorAlert(@"Python/PyObjC program failed to start.\nSee Console.app for details.");
        return -1;
    }
}
