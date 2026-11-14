import XCTest
@testable import MorpherCore

final class DelaunayTests: XCTestCase {

    func testSquareProducesTwoTriangles() {
        let pts = [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)]
        let tris = Delaunay.triangulate(pts)
        XCTAssertEqual(tris.count, 2)
    }

    func testSquarePlusCenterProducesFourTriangles() {
        let pts = [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10), Point(5, 5)]
        let tris = Delaunay.triangulate(pts)
        XCTAssertEqual(tris.count, 4)
    }

    func testInCircumcircle() {
        // Equilateral-ish CCW triangle.
        let a = Point(0, 0), b = Point(2, 0), c = Point(1, 1.732)
        XCTAssertTrue(Delaunay.inCircumcircle(a, b, c, Point(1, 0.5)), "center should be inside")
        XCTAssertFalse(Delaunay.inCircumcircle(a, b, c, Point(1, 2)), "above apex should be outside")
        XCTAssertFalse(Delaunay.inCircumcircle(a, b, c, Point(5, 5)), "far point should be outside")
        XCTAssertFalse(Delaunay.inCircumcircle(a, b, c, a), "vertex is not strictly inside")
    }

    func testTriangulationIsValidOnRandomPoints() {
        var rng = LCG(seed: 42)
        var pts: [Point] = []
        var seen = Set<Point>()
        while pts.count < 12 {
            let p = Point(Double(Int.random(in: 0..<100, using: &rng)),
                          Double(Int.random(in: 0..<100, using: &rng)))
            if seen.insert(p).inserted { pts.append(p) }
        }

        let tris = Delaunay.triangulate(pts)
        XCTAssertFalse(tris.isEmpty)

        for t in tris {
            XCTAssertTrue(t.a >= 0 && t.a < pts.count, "index out of range: \(t)")
            XCTAssertTrue(t.b >= 0 && t.b < pts.count, "index out of range: \(t)")
            XCTAssertTrue(t.c >= 0 && t.c < pts.count, "index out of range: \(t)")
            XCTAssertTrue(t.a != t.b && t.b != t.c && t.c != t.a, "degenerate triangle: \(t)")
        }
        XCTAssertEqual(Set(tris).count, tris.count, "duplicate triangles")
    }

    func testDelaunayEmptyCircumcircleOnRandomPoints() {
        var rng = LCG(seed: 1337)
        var pts: [Point] = []
        var seen = Set<Point>()
        while pts.count < 15 {
            let p = Point(Double(Int.random(in: 0..<1000, using: &rng)),
                          Double(Int.random(in: 0..<1000, using: &rng)))
            if seen.insert(p).inserted { pts.append(p) }
        }

        let tris = Delaunay.triangulate(pts)
        for t in tris {
            let (a, b, c) = (pts[t.a], pts[t.b], pts[t.c])
            for (i, p) in pts.enumerated() where i != t.a && i != t.b && i != t.c {
                XCTAssertFalse(
                    Delaunay.inCircumcircle(a, b, c, p),
                    "point \(p) violates Delaunay condition for triangle \(t)"
                )
            }
        }
    }
}

/// Minimal deterministic pseudo-random generator for reproducible tests.
struct LCG: RandomNumberGenerator {
    private var state: UInt64

    init(seed: UInt64) {
        self.state = seed
    }

    mutating func next() -> UInt64 {
        state = state &* 6364136223846793005 &+ 1442695040888963407
        return state
    }
}
