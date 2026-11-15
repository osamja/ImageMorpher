import XCTest

@testable import MorpherCore

final class StillExporterTests: XCTestCase {
    func testPNGRoundTrip() throws {
        let image = TestSupport.gradientImage(width: 16, height: 12)
        let data = try StillExporter.pngData(from: image)
        let loaded = try ImageLoader.load(data: data, maxPixelSize: 100)

        XCTAssertEqual(loaded.width, 16)
        XCTAssertEqual(loaded.height, 12)
        XCTAssertEqual(loaded, image)
    }

    func testWritePNGToDisk() throws {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathExtension("png")
        defer {
            try? FileManager.default.removeItem(at: url)
        }

        let image = TestSupport.gradientImage(width: 8, height: 8)
        try StillExporter.writePNG(image, to: url)

        XCTAssertTrue(FileManager.default.fileExists(atPath: url.path))
        XCTAssertEqual(
            try ImageLoader.load(contentsOf: url, maxPixelSize: 100),
            image
        )
    }
}
