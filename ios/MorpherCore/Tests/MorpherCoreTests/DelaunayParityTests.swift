import XCTest
@testable import MorpherCore

final class DelaunayParityTests: XCTestCase {

    /// The Swift Bowyer–Watson triangulation must exactly match scipy's
    /// `Delaunay` (Qhull) on a general-position point set where the Delaunay
    /// triangulation is unique.
    func testMatchesScipyDelaunay() {
        let tris = Delaunay.triangulate(ParityFixture.points)
        let normalized = Set(tris.map { [$0.a, $0.b, $0.c].sorted() })
        let expected = Set(ParityFixture.expectedTriangles)

        XCTAssertEqual(normalized.count, expected.count, "triangle count differs")
        XCTAssertEqual(normalized, expected, "triangulation differs from scipy")
    }
}
