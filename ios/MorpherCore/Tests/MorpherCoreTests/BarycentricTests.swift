import XCTest
@testable import MorpherCore

final class BarycentricTests: XCTestCase {

    private let a = Point(0, 0)
    private let b = Point(10, 0)
    private let c = Point(0, 10)

    func testVertexA() {
        let bc = Barycentric.coordinates(a, a, b, c)
        XCTAssertEqual(bc.u, 1.0, accuracy: 1e-9)
        XCTAssertEqual(bc.v, 0.0, accuracy: 1e-9)
        XCTAssertEqual(bc.w, 0.0, accuracy: 1e-9)
    }

    func testCentroid() {
        let bc = Barycentric.coordinates(Point(10.0 / 3.0, 10.0 / 3.0), a, b, c)
        XCTAssertEqual(bc.u, 1.0 / 3.0, accuracy: 1e-9)
        XCTAssertEqual(bc.v, 1.0 / 3.0, accuracy: 1e-9)
        XCTAssertEqual(bc.w, 1.0 / 3.0, accuracy: 1e-9)
    }

    func testOutsidePointIsRejected() {
        let bc = Barycentric.coordinates(Point(9, 9), a, b, c)
        XCTAssertFalse(Barycentric.isInside(bc))
    }

    func testInsidePointIsAccepted() {
        let bc = Barycentric.coordinates(Point(2, 2), a, b, c)
        XCTAssertTrue(Barycentric.isInside(bc))
    }
}
