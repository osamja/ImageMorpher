import XCTest

@testable import MorpherCore

final class ImageLoaderTests: XCTestCase {
    func testLoadsJPEG() throws {
        let image = try ImageLoader.load(
            contentsOf: TestSupport.inputImage("1.jpeg")
        )

        XCTAssertEqual(image.width, 100)
        XCTAssertEqual(image.height, 85)
        XCTAssertTrue(image.pixels.contains { $0 != 0 })
    }

    func testLoadsPNG() throws {
        let image = try ImageLoader.load(
            contentsOf: TestSupport.inputImage("will-smith.png")
        )

        XCTAssertEqual(max(image.width, image.height), 600)
        XCTAssertEqual(
            Double(image.width) / Double(image.height),
            689.0 / 937.0,
            accuracy: 0.01
        )
    }

    func testLoadsHEIC() throws {
        let image = try ImageLoader.load(
            contentsOf: TestSupport.inputImage("sammy-selfie.HEIC"),
            maxPixelSize: 300
        )

        XCTAssertEqual(max(image.width, image.height), 300)
        XCTAssertTrue(image.pixels.contains { $0 != 0 })
    }

    func testDownsamplesToMaxPixelSize() throws {
        let image = try ImageLoader.load(
            contentsOf: TestSupport.inputImage("face-1.jpeg"),
            maxPixelSize: 200
        )

        XCTAssertEqual(max(image.width, image.height), 200)
        XCTAssertEqual(
            Double(image.width) / Double(image.height),
            500.0 / 427.0,
            accuracy: 0.02
        )
    }

    func testRejectsInvalidThumbnailSize() {
        XCTAssertThrowsError(
            try ImageLoader.load(
                contentsOf: TestSupport.inputImage("1.jpeg"),
                maxPixelSize: 0
            )
        ) { error in
            XCTAssertEqual(
                error as? ImageLoaderError,
                .invalidThumbnailSize(0)
            )
        }
    }

    func testPNGDecodePreservesTopDownOrientation() throws {
        let source = try TestSupport.makeColorfulCGImage()
        let data = try TestSupport.pngData(for: source)
        let image = try ImageLoader.load(data: data, maxPixelSize: 2)

        XCTAssertEqual(image.width, 2)
        XCTAssertEqual(image.height, 2)
        XCTAssertEqual(image.pixel(x: 0, y: 0), RGBA(r: 255, g: 0, b: 0))
        XCTAssertEqual(image.pixel(x: 1, y: 0), RGBA(r: 0, g: 255, b: 0))
        XCTAssertEqual(image.pixel(x: 0, y: 1), RGBA(r: 0, g: 0, b: 255))
        XCTAssertEqual(image.pixel(x: 1, y: 1), RGBA(r: 255, g: 255, b: 255))
    }
}
