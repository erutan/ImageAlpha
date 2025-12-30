//
//  main.m
//  ImageAlpha

#import <Python/Python.h>
#import <Cocoa/Cocoa.h>
#import "IAColorBackgroundRenderer.h"
#import "IAPatternBackgroundRenderer.h"
#import <errno.h>
#import <fcntl.h>
#import <string.h>
#import <unistd.h>

static void ShowPythonErrorAlert(NSString *message)
{
    NSAlert *alert = [[NSAlert alloc] init];
    alert.messageText = @"Unable to start ImageAlpha";
    alert.informativeText = message;
    [alert addButtonWithTitle:@"Abort"];
    [alert runModal];
    [alert release];
}

static void LogMessage(const char *message)
{
    if (message && stderr) {
        fprintf(stderr, "%s\n", message);
        fflush(stderr);
    }
}

static void LogStatus(const char *context, PyStatus status)
{
    if (!stderr || !context) return;
    if (PyStatus_IsExit(status)) {
        fprintf(stderr, "%s: exitcode=%d\n", context, status.exitcode);
    } else if (PyStatus_Exception(status)) {
        fprintf(stderr, "%s: %s\n", context, status.err_msg ? status.err_msg : "unknown error");
    } else {
        fprintf(stderr, "%s: ok\n", context);
    }
    fflush(stderr);
}

int main(int argc, char *argv[])
{
    @autoreleasepool {
        NSBundle *mainBundle = [NSBundle mainBundle];
        NSString *frameworksPath = [mainBundle privateFrameworksPath];
        NSString *resourcePath = [mainBundle resourcePath];
        NSString *pythonHome = nil;
        NSString *logPath = @"/tmp/ImageAlpha-python.log";
        const char *statusContext = NULL;

        // Ensure Objective-C classes used via NSClassFromString are linked.
        [IAColorBackgroundRenderer class];
        [IAPatternBackgroundRenderer class];

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

        int logFd = open([logPath fileSystemRepresentation], O_CREAT | O_TRUNC | O_WRONLY, 0644);
        if (logFd >= 0) {
            dup2(logFd, STDERR_FILENO);
            dup2(logFd, STDOUT_FILENO);
            close(logFd);
            setvbuf(stderr, NULL, _IONBF, 0);
            fprintf(stderr, "ImageAlpha Python bootstrap\n");
            fprintf(stderr, "pythonHome=%s\n", [pythonHome fileSystemRepresentation]);
            fprintf(stderr, "resourcePath=%s\n", [resourcePath fileSystemRepresentation]);
            fprintf(stderr, "mainFilePath=%s\n", [mainFilePath fileSystemRepresentation]);
            fflush(stderr);
        } else {
            NSLog(@"Failed to open log at %@: %s", logPath, strerror(errno));
        }

        PyStatus status;
        PyConfig config;
        PyConfig_InitPythonConfig(&config);
        config.isolated = 0;
        config.use_environment = 0;
        config.user_site_directory = 0;
        config.site_import = 1;

        status = PyConfig_SetBytesString(&config, &config.home, [pythonHome fileSystemRepresentation]);
        if (PyStatus_Exception(status)) {
            statusContext = "PyConfig_SetBytesString(home)";
            LogStatus(statusContext, status);
            goto python_error;
        }
        LogMessage("PyConfig_SetBytesString(home) ok");

        status = PyConfig_Read(&config);
        if (PyStatus_Exception(status)) {
            statusContext = "PyConfig_Read";
            LogStatus(statusContext, status);
            goto python_error;
        }
        LogMessage("PyConfig_Read ok");

        NSString *pythonLibPath = [pythonHome stringByAppendingPathComponent:@"lib/python3.13"];
        NSString *pythonDynloadPath = [pythonLibPath stringByAppendingPathComponent:@"lib-dynload"];
        NSString *pythonSitePath = [pythonLibPath stringByAppendingPathComponent:@"site-packages"];

        NSArray *modulePaths = [NSArray arrayWithObjects:
                                pythonLibPath,
                                pythonDynloadPath,
                                pythonSitePath,
                                resourcePath,
                                nil];
        for (NSString *path in modulePaths) {
            if (!path) continue;
            wchar_t *pathW = Py_DecodeLocale([path fileSystemRepresentation], NULL);
            if (!pathW) {
                statusContext = "Py_DecodeLocale(module_search_path)";
                goto python_error;
            }
            status = PyWideStringList_Append(&config.module_search_paths, pathW);
            PyMem_RawFree(pathW);
            if (PyStatus_Exception(status)) {
                statusContext = "PyWideStringList_Append(module_search_path)";
                LogStatus(statusContext, status);
                goto python_error;
            }
        }
        config.module_search_paths_set = 1;

        if (stderr && config.module_search_paths.length > 0) {
            fprintf(stderr, "module_search_paths:\n");
            for (Py_ssize_t i = 0; i < config.module_search_paths.length; i++) {
                wchar_t *item = config.module_search_paths.items[i];
                if (item) {
                    fprintf(stderr, "  %ls\n", item);
                }
            }
            fflush(stderr);
        }

        status = PyConfig_SetBytesString(&config, &config.run_filename, [mainFilePath fileSystemRepresentation]);
        if (PyStatus_Exception(status)) {
            statusContext = "PyConfig_SetBytesString(run_filename)";
            LogStatus(statusContext, status);
            goto python_error;
        }
        LogMessage("PyConfig_SetBytesString(run_filename) ok");

        status = PyConfig_SetBytesArgv(&config, argc, argv);
        if (PyStatus_Exception(status)) {
            statusContext = "PyConfig_SetBytesArgv";
            LogStatus(statusContext, status);
            goto python_error;
        }
        LogMessage("PyConfig_SetBytesArgv ok");

        status = Py_InitializeFromConfig(&config);
        if (PyStatus_Exception(status)) {
            statusContext = "Py_InitializeFromConfig";
            LogStatus(statusContext, status);
            goto python_error;
        }
        LogMessage("Py_InitializeFromConfig ok");

        PyConfig_Clear(&config);
        int runResult = Py_RunMain();
        if (stderr) {
            fprintf(stderr, "Py_RunMain returned %d\n", runResult);
            fflush(stderr);
        }
        if (runResult != 0) {
            ShowPythonErrorAlert([NSString stringWithFormat:@"Python/PyObjC program failed to start.\nSee %@ for details.", logPath]);
        }
        return runResult;

python_error:
        PyConfig_Clear(&config);
        if (statusContext) {
            LogStatus(statusContext, status);
        }
        {
            const char *errMsg = status.err_msg ? status.err_msg : "unknown error";
            NSString *context = statusContext ? [NSString stringWithUTF8String:statusContext] : @"unknown";
            NSString *detail = [NSString stringWithFormat:@"Python/PyObjC program failed to start (%@): %s\nSee %@ for details.",
                                context, errMsg, logPath];
            ShowPythonErrorAlert(detail);
        }
        return -1;
    }
}
