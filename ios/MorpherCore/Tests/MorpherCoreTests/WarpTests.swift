import XCTest
@testable import MorpherCore

final class WarpTests: XCTestCase {

    private func makeGradientImage() -> ImageBuffer {
        var img = ImageBuffer(width: 32, height: 32)
        for y in 0..<32 {
            for x in 0..<32 {
                img.setPixel(x: x, y: y,
                             r: UInt8((x * 8) % 256),
                             g: UInt8((y * 8) % 256),
                             b: UInt8(((x + y) * 4) % 256))
            }
        }
        return img
    }

    private func assertImagesEqual(_ a: ImageBuffer, _ b: ImageBuffer, file: StaticString = #filePath, line: UInt = #line) {
        XCTAssertEqual(a.width, b.width, file: file, line: line)
        XCTAssertEqual(a.height, b.height, file: file, line: line)
        guard a.width == b.width, a.height == b.height else { return }
        var diffs = 0
        for y in 0..<a.height {
            for x in 0..<a.width {
                let pa = a.pixel(x: x, y: y)
                let pb = b.pixel(x: x, y: y)
                if pa.r != pb.r || pa.g != pb.g || pa.b != pb.b || pa.a != pb.a { diffs += 1 }
            }
        }
        XCTAssertEqual(diffs, 0, "\(diffs) pixels differ", file: file, line: line)
    }

    func testIdentityWarpReproducesImage() {
        let img = makeGradientImage()
        var pts = CornerPoints.add(to: [Point(16, 16), Point(8, 8), Point(24, 20)], width: 32, height: 32)
        let triangles = Delaunay.triangulate(pts)

        let warped = AffineWarp.warp(source: img, sourcePoints: pts, targetPoints: pts, triangles: triangles)
        assertImagesEqual(warped, img)
    }

    func testWarpMovesAColoredRegion() {
        // A solid blue square in the bottom-left that should be warped to a
        // new location. Source triangle in the bottom-left, target triangle in
        // the top-right.
        var src = ImageBuffer(width: 32, height: 32, color: (r: 0, g: 0, b: 0))
        for y in 16..<32 {
            for x in 0..<16 { src.setPixel(x: x, y: y, r: 0, g: 0, b: 255) }
        }

        let sourcePts = [Point(0, 31), Point(15, 31), Point(0, 16)]
        let targetPts = [Point(31, 0), Point(16, 0), Point(31, 15)]
        let triangles = [Triangle(0, 1, 2)]

        let warped = AffineWarp.warp(source: src, sourcePoints: sourcePts, targetPoints: targetPts, triangles: triangles)

        // The top-right region should now contain blue.
        let sample = warped.pixel(x: 24, y: 8)
        XCTAssertEqual(sample.b, 255, "blue should have moved to top-right")
    }
}
