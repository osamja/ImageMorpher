import XCTest

@testable import MorpherCore

final class DissolveTests: XCTestCase {
    private let first = ImageBuffer(
        width: 1,
        height: 1,
        fill: RGBA(r: 255, g: 0, b: 100, a: 255)
    )
    private let second = ImageBuffer(
        width: 1,
        height: 1,
        fill: RGBA(r: 0, g: 255, b: 200, a: 255)
    )

    func testEndpointsReturnInputs() throws {
        XCTAssertEqual(
            try Dissolve.blend(first, second, t: 0),
            first
        )
        XCTAssertEqual(
            try Dissolve.blend(first, second, t: 1),
            second
        )
    }

    func testHalfwayBlendUsesTruncation() throws {
        let blended = try Dissolve.blend(first, second, t: 0.5)

        XCTAssertEqual(
            blended[0, 0],
            RGBA(r: 127, g: 127, b: 150, a: 254)
        )
    }

    func testQuarterBlend() throws {
        let blended = try Dissolve.blend(first, second, t: 0.25)

        XCTAssertEqual(
            blended[0, 0],
            RGBA(r: 191, g: 63, b: 125, a: 254)
        )
    }

    func testSizeMismatchThrows() {
        let smaller = ImageBuffer(width: 1, height: 1, fill: .black)

        XCTAssertThrowsError(
            try Dissolve.blend(
                ImageBuffer(width: 2, height: 2, fill: .black),
                smaller,
                t: 0.5
            )
        ) { error in
            XCTAssertEqual(error as? MorpherError, .imageSizeMismatch)
        }
    }
}
