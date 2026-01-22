import XCTest

class CompressionSettingsTests: XCTestCase {

    func testCompressionSettings() throws {
        // Find the Python framework and test script
        let projectDir = URL(fileURLWithPath: #file)
            .deletingLastPathComponent()  // ImageAlphaTests
            .deletingLastPathComponent()  // ImageAlpha

        let pythonPath = projectDir
            .appendingPathComponent("Frameworks")
            .appendingPathComponent("Python.framework")
            .appendingPathComponent("Versions")
            .appendingPathComponent("3.13")
            .appendingPathComponent("bin")
            .appendingPathComponent("python3")

        let testScript = projectDir
            .appendingPathComponent("test_compression_settings.py")

        // Verify files exist
        XCTAssertTrue(FileManager.default.fileExists(atPath: pythonPath.path),
                      "Python framework not found at \(pythonPath.path)")
        XCTAssertTrue(FileManager.default.fileExists(atPath: testScript.path),
                      "Test script not found at \(testScript.path)")

        // Run the Python tests
        let process = Process()
        process.executableURL = pythonPath
        process.arguments = [testScript.path]
        process.currentDirectoryURL = projectDir

        let outputPipe = Pipe()
        let errorPipe = Pipe()
        process.standardOutput = outputPipe
        process.standardError = errorPipe

        try process.run()
        process.waitUntilExit()

        let outputData = outputPipe.fileHandleForReading.readDataToEndOfFile()
        let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()

        let output = String(data: outputData, encoding: .utf8) ?? ""
        let errorOutput = String(data: errorData, encoding: .utf8) ?? ""

        // Print output for visibility in Xcode console
        print(output)
        if !errorOutput.isEmpty {
            print("STDERR: \(errorOutput)")
        }

        // Check exit code
        XCTAssertEqual(process.terminationStatus, 0,
                       "Python tests failed with exit code \(process.terminationStatus)\n\(output)")

        // Also verify the output contains expected success message
        XCTAssertTrue(output.contains("0 failed"),
                      "Tests did not all pass:\n\(output)")
    }
}
