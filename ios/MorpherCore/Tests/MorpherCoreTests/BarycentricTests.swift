import XCTest

@testable import MorpherCore

final class BarycentricTests: XCTestCase {
    private let unitTriangle = TriangleVertices(
        a: SIMD2<Double>(0, 0),
        b: SIMD2<Double>(1, 0),
        c: SIMD2<Double>(0, 1)
    )

    func testVerticesMapToBasisVectors() throws {
        let a = try XCTUnwrap(
            Barycentric.coordinates(of: unitTriangle.a, in: unitTriangle)
        )
        let b = try XCTUnwrap(
            Barycentric.coordinates(of: unitTriangle.b, in: unitTriangle)
        )
        let c = try XCTUnwrap(
            Barycentric.coordinates(of: unitTriangle.c, in: unitTriangle)
        )

        assertEqual(a, SIMD3<Double>(1, 0, 0))
        assertEqual(b, SIMD3<Double>(0, 1, 0))
        assertEqual(c, SIMD3<Double>(0, 0, 1))
    }

    func testCentroidAndInteriorPoint() throws {
        let centroid = try XCTUnwrap(
            Barycentric.coordinates(
                of: SIMD2<Double>(1.0 / 3.0, 1.0 / 3.0),
                in: unitTriangle
            )
        )
        assertEqual(
            centroid,
            SIMD3<Double>(1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
        )

        let point = try XCTUnwrap(
            Barycentric.coordinates(
                of: SIMD2<Double>(0.25, 0.25),
                in: unitTriangle
            )
        )
        assertEqual(point, SIMD3<Double>(0.5, 0.25, 0.25))
    }

    func testContainsInsideOutsideAndBoundary() {
        XCTAssertTrue(
            Barycentric.contains(SIMD2<Double>(0.25, 0.25), in: unitTriangle)
        )
        XCTAssertTrue(
            Barycentric.contains(SIMD2<Double>(0.5, 0), in: unitTriangle)
        )
        XCTAssertTrue(
            Barycentric.contains(unitTriangle.a, in: unitTriangle)
        )
        XCTAssertFalse(
            Barycentric.contains(SIMD2<Double>(0.75, 0.75), in: unitTriangle)
        )
        XCTAssertFalse(
            Barycentric.contains(SIMD2<Double>(-0.01, 0.5), in: unitTriangle)
        )
    }

    func testDegenerateTriangleHasNoCoordinates() {
        let degenerate = TriangleVertices(
            a: SIMD2<Double>(0, 0),
            b: SIMD2<Double>(1, 1),
            c: SIMD2<Double>(2, 2)
        )

        XCTAssertNil(
            Barycentric.coordinates(of: SIMD2<Double>(0.5, 0.5), in: degenerate)
        )
        XCTAssertFalse(
            Barycentric.contains(SIMD2<Double>(0.5, 0.5), in: degenerate)
        )
        XCTAssertNil(AffineMap.mapping(from: degenerate, to: unitTriangle))
    }

    func testInterpolationReconstructsPoint() throws {
        let point = SIMD2<Double>(0.2, 0.3)
        let weights = try XCTUnwrap(
            Barycentric.coordinates(of: point, in: unitTriangle)
        )
        let reconstructed = Barycentric.interpolate(weights, in: unitTriangle)

        XCTAssertEqual(reconstructed.x, point.x, accuracy: 1e-12)
        XCTAssertEqual(reconstructed.y, point.y, accuracy: 1e-12)
    }

    func testAffineMapMapsVerticesAndRoundTrips() throws {
        let destination = TriangleVertices(
            a: SIMD2<Double>(2, 3),
            b: SIMD2<Double>(5, 3),
            c: SIMD2<Double>(2, 7)
        )
        let map = try XCTUnwrap(
            AffineMap.mapping(from: unitTriangle, to: destination)
        )

        let pairs = [
            (unitTriangle.a, destination.a),
            (unitTriangle.b, destination.b),
            (unitTriangle.c, destination.c),
        ]
        for (source, expected) in pairs {
            let actual = map.apply(to: source)
            XCTAssertEqual(actual.x, expected.x, accuracy: 1e-12)
            XCTAssertEqual(actual.y, expected.y, accuracy: 1e-12)
        }

        let midpoint = SIMD2<Double>(0.25, 0.25)
        let mappedMidpoint = map.apply(to: midpoint)
        XCTAssertEqual(mappedMidpoint.x, 2.75, accuracy: 1e-12)
        XCTAssertEqual(mappedMidpoint.y, 4.0, accuracy: 1e-12)

        let inverse = try XCTUnwrap(map.inverted)
        let roundTripped = inverse.apply(to: mappedMidpoint)
        XCTAssertEqual(roundTripped.x, midpoint.x, accuracy: 1e-12)
        XCTAssertEqual(roundTripped.y, midpoint.y, accuracy: 1e-12)
    }

    private func assertEqual(
        _ lhs: SIMD3<Double>,
        _ rhs: SIMD3<Double>,
        accuracy: Double = 1e-12,
        file: StaticString = #filePath,
        line: UInt = #line
    ) {
        XCTAssertEqual(lhs.x, rhs.x, accuracy: accuracy, file: file, line: line)
        XCTAssertEqual(lhs.y, rhs.y, accuracy: accuracy, file: file, line: line)
        XCTAssertEqual(lhs.z, rhs.z, accuracy: accuracy, file: file, line: line)
    }
}
