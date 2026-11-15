import Foundation
import XCTest

@testable import MorpherCore

final class DelaunayTests: XCTestCase {
    private struct Fixture: Decodable {
        let name: String
        let points: [[Double]]
        let simplices: [[Int]]
    }

    func testSingleTriangle() {
        let points = [
            SIMD2<Double>(0, 0),
            SIMD2<Double>(1, 0),
            SIMD2<Double>(0, 1),
        ]

        let triangles = Delaunay.triangulate(points)

        XCTAssertEqual(triangles.count, 1)
        XCTAssertEqual(Set(triangles[0].indices), Set([0, 1, 2]))
    }

    func testSquareProducesTwoTriangles() {
        let points = [
            SIMD2<Double>(0, 0),
            SIMD2<Double>(10, 0),
            SIMD2<Double>(10, 10),
            SIMD2<Double>(0, 10),
        ]

        let triangles = Delaunay.triangulate(points)

        XCTAssertEqual(triangles.count, 2)
        XCTAssertEqual(Set(triangles.flatMap(\.indices)), Set(0..<4))

        let actual = Set(triangles.map(\.sortedIndices))
        let firstDiagonal = Set([[0, 1, 2], [0, 2, 3]])
        let secondDiagonal = Set([[0, 1, 3], [1, 2, 3]])
        XCTAssertTrue(actual == firstDiagonal || actual == secondDiagonal)
    }

    func testCollinearPointsProduceNoTriangles() {
        let points = (0..<5).map { SIMD2<Double>(Double($0), 0) }

        XCTAssertTrue(Delaunay.triangulate(points).isEmpty)
    }

    func testDuplicatePointsAreMerged() {
        let points = [
            SIMD2<Double>(0, 0),
            SIMD2<Double>(1, 0),
            SIMD2<Double>(0, 1),
            SIMD2<Double>(0, 0),
        ]

        let triangles = Delaunay.triangulate(points)

        XCTAssertEqual(triangles.count, 1)
        XCTAssertEqual(triangles[0].sortedIndices, [0, 1, 2])
    }

    func testTooFewPoints() {
        XCTAssertTrue(Delaunay.triangulate([]).isEmpty)
        XCTAssertTrue(
            Delaunay.triangulate([
                SIMD2<Double>(0, 0),
                SIMD2<Double>(1, 1),
            ]).isEmpty
        )
    }

    func testNonFinitePointsAreIgnored() {
        let points = [
            SIMD2<Double>(0, 0),
            SIMD2<Double>(.nan, 1),
            SIMD2<Double>(1, 0),
            SIMD2<Double>(0, .infinity),
            SIMD2<Double>(0, 1),
        ]

        let triangles = Delaunay.triangulate(points)

        XCTAssertEqual(triangles.count, 1)
        XCTAssertEqual(Set(triangles[0].indices), Set([0, 2, 4]))
    }

    func testParityWithScipyFixtures() throws {
        let fixtures = [
            "delaunay_uniform_20",
            "delaunay_uniform_73",
            "delaunay_uniform_200",
        ]

        for name in fixtures {
            let fixture = try loadFixture(named: name)
            let points = fixture.points.map { SIMD2<Double>($0[0], $0[1]) }
            let actual = Set(
                Delaunay.triangulate(points).map(\.sortedIndices)
            )
            let expected = Set(fixture.simplices.map { $0.sorted() })

            XCTAssertEqual(
                actual,
                expected,
                "\(name): missing \(expected.subtracting(actual)), extra \(actual.subtracting(expected))"
            )
        }
    }

    func testTriangulationSatisfiesEmptyCircumcircleProperty() {
        var state: UInt64 = 0x9E37_79B9_7F4A_7C15
        func next() -> Double {
            state = state &* 6_364_136_223_846_793_005 &+ 1_442_695_040_888_963_407
            return Double(state >> 11) / Double(UInt64(1) << 53)
        }
        let points = (0..<50).map { _ in
            SIMD2<Double>(next() * 500, next() * 500)
        }

        let triangles = Delaunay.triangulate(points)
        XCTAssertFalse(triangles.isEmpty)

        for triangle in triangles {
            let a = points[triangle.a]
            let b = points[triangle.b]
            let c = points[triangle.c]
            XCTAssertGreaterThan(
                Delaunay.orientation(a, b, c),
                0,
                "triangle must be counter-clockwise"
            )

            for index in points.indices where !triangle.indices.contains(index) {
                XCTAssertFalse(
                    isInCircumcircle(points[index], a, b, c),
                    "point \(index) is inside circumcircle of \(triangle.indices)"
                )
            }
        }
    }

    private func loadFixture(named name: String) throws -> Fixture {
        let url = try TestSupport.fixtureURL(named: name)
        let data = try Data(contentsOf: url)
        return try JSONDecoder().decode(Fixture.self, from: data)
    }

    private func isInCircumcircle(
        _ point: SIMD2<Double>,
        _ a: SIMD2<Double>,
        _ b: SIMD2<Double>,
        _ c: SIMD2<Double>
    ) -> Bool {
        let adx = a.x - point.x
        let ady = a.y - point.y
        let bdx = b.x - point.x
        let bdy = b.y - point.y
        let cdx = c.x - point.x
        let cdy = c.y - point.y

        let abdet = adx * bdy - bdx * ady
        let bcdet = bdx * cdy - cdx * bdy
        let cadet = cdx * ady - adx * cdy
        let alift = adx * adx + ady * ady
        let blift = bdx * bdx + bdy * bdy
        let clift = cdx * cdx + cdy * cdy

        return alift * bcdet + blift * cadet + clift * abdet > 0
    }
}
