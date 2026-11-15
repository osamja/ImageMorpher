import XCTest

@testable import MorpherCore

final class ImageBufferTests: XCTestCase {
    func testFillAndPixelAccess() {
        var buffer = ImageBuffer(
            width: 2,
            height: 2,
            fill: RGBA(r: 10, g: 20, b: 30)
        )

        XCTAssertEqual(buffer.width, 2)
        XCTAssertEqual(buffer.height, 2)
        XCTAssertEqual(buffer.bytesPerRow, 8)
        XCTAssertEqual(buffer.byteCount, 16)
        XCTAssertEqual(buffer.pixel(x: 0, y: 0), RGBA(r: 10, g: 20, b: 30))
        XCTAssertEqual(buffer.pixel(x: 1, y: 1), RGBA(r: 10, g: 20, b: 30))

        buffer.setPixel(RGBA(r: 1, g: 2, b: 3), x: 1, y: 1)

        XCTAssertEqual(buffer.pixel(x: 1, y: 1), RGBA(r: 1, g: 2, b: 3))
        XCTAssertEqual(buffer.pixel(x: 0, y: 1), RGBA(r: 10, g: 20, b: 30))
        XCTAssertEqual(buffer[0, 0], RGBA(r: 10, g: 20, b: 30))
        XCTAssertNil(buffer.pixel(x: -1, y: 0))
        XCTAssertNil(buffer.pixel(x: 0, y: 2))
    }

    func testInitRejectsMismatchedPixelCount() {
        XCTAssertThrowsError(
            try ImageBuffer(width: 2, height: 2, pixels: [0, 0, 0, 255])
        ) { error in
            XCTAssertEqual(
                error as? ImageBufferError,
                .invalidPixelCount(expected: 16, actual: 4)
            )
        }
    }

    func testInitRejectsInvalidDimensions() {
        XCTAssertThrowsError(
            try ImageBuffer(width: 0, height: 2, pixels: [])
        ) { error in
            XCTAssertEqual(
                error as? ImageBufferError,
                .invalidDimensions(width: 0, height: 2)
            )
        }
    }

    func testCGImageRoundTripPreservesTopDownOrientation() throws {
        let image = try TestSupport.makeColorfulCGImage()
        let buffer = try ImageBuffer(cgImage: image)

        XCTAssertEqual(buffer.width, 2)
        XCTAssertEqual(buffer.height, 2)
        XCTAssertEqual(buffer.pixel(x: 0, y: 0), RGBA(r: 255, g: 0, b: 0))
        XCTAssertEqual(buffer.pixel(x: 1, y: 0), RGBA(r: 0, g: 255, b: 0))
        XCTAssertEqual(buffer.pixel(x: 0, y: 1), RGBA(r: 0, g: 0, b: 255))
        XCTAssertEqual(buffer.pixel(x: 1, y: 1), RGBA(r: 255, g: 255, b: 255))

        let roundTrippedImage = try XCTUnwrap(buffer.makeCGImage())
        let roundTrippedBuffer = try ImageBuffer(cgImage: roundTrippedImage)
        XCTAssertEqual(roundTrippedBuffer, buffer)
    }
}
