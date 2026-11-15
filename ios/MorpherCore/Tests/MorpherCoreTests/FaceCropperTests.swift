import XCTest

@testable import MorpherCore

final class FaceCropperTests: XCTestCase {
    func testCropsFaceToCanonicalSize() throws {
        let image = try ImageLoader.load(
            contentsOf: TestSupport.inputImage("face-1.jpeg")
        )
        let cropped = try FaceCropper().crop(image)

        XCTAssertEqual(cropped.width, 500)
        XCTAssertEqual(cropped.height, 500)
        XCTAssertGreaterThan(Set(cropped.pixels).count, 16)
    }

    func testCropsFaceAtCustomSize() throws {
        let image = try ImageLoader.load(
            contentsOf: TestSupport.inputImage("face-1.jpeg")
        )
        let cropped = try FaceCropper(outputSize: 200).crop(image)

        XCTAssertEqual(cropped.width, 200)
        XCTAssertEqual(cropped.height, 200)
    }

    func testThrowsWhenNoFaceDetected() {
        let blank = ImageBuffer(
            width: 64,
            height: 64,
            fill: RGBA(r: 128, g: 128, b: 128)
        )

        XCTAssertThrowsError(try FaceCropper().crop(blank)) { error in
            XCTAssertEqual(error as? FaceCropperError, .noFaceDetected)
        }
    }
}
