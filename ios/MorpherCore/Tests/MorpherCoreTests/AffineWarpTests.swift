import XCTest

@testable import MorpherCore

final class AffineWarpTests: XCTestCase {
    func testIdentityWarpReproducesImage() throws {
        let image = TestSupport.gradientImage(width: 24, height: 18)
        let points = TestSupport.gridPoints(
            width: 24,
            height: 18,
            columns: 3,
            rows: 3
        )
        let triangles = Delaunay.triangulate(points)

        XCTAssertFalse(triangles.isEmpty)

        let warped = try AffineWarp().warp(
            image: image,
            sourcePoints: points,
            destinationPoints: points,
            triangles: triangles
        )

        XCTAssertEqual(warped, image)
    }

    func testTranslationSamplesShiftedPixels() throws {
        var image = ImageBuffer(width: 6, height: 6)
        for y in 0..<6 {
            for x in 0..<6 {
                image[x, y] = RGBA(
                    r: UInt8(x * 20),
                    g: UInt8(y * 20),
                    b: 0
                )
            }
        }

        let source = [
            SIMD2<Double>(0, 0),
            SIMD2<Double>(6, 0),
            SIMD2<Double>(0, 6),
        ]
        let destination = [
            SIMD2<Double>(1, 1),
            SIMD2<Double>(7, 1),
            SIMD2<Double>(1, 7),
        ]
        let triangle = Triangle(0, 1, 2)

        let warped = try AffineWarp().warp(
            image: image,
            sourcePoints: source,
            destinationPoints: destination,
            triangles: [triangle]
        )

        XCTAssertEqual(warped[1, 1], image[0, 0])
        XCTAssertEqual(warped[3, 2], image[2, 1])
        XCTAssertEqual(warped[5, 1], image[4, 0])
        XCTAssertEqual(warped[0, 0], RGBA.black)
    }

    func testMismatchedPointCountsThrow() {
        let image = TestSupport.solidImage(
            width: 4,
            height: 4,
            color: .black
        )

        XCTAssertThrowsError(
            try AffineWarp().warp(
                image: image,
                sourcePoints: [SIMD2(0, 0), SIMD2(1, 0), SIMD2(0, 1)],
                destinationPoints: [SIMD2(0, 0)],
                triangles: []
            )
        ) { error in
            XCTAssertEqual(error as? MorpherError, .landmarkCountMismatch)
        }
    }

    func testInvalidTriangleThrows() {
        let image = TestSupport.solidImage(
            width: 4,
            height: 4,
            color: .black
        )
        let points = [SIMD2<Double>(0, 0), SIMD2(1, 0), SIMD2(0, 1)]

        XCTAssertThrowsError(
            try AffineWarp().warp(
                image: image,
                sourcePoints: points,
                destinationPoints: points,
                triangles: [Triangle(0, 1, 5)]
            )
        ) { error in
            XCTAssertEqual(error as? MorpherError, .invalidTriangle(index: 0))
        }
    }
}
