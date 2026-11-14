import Foundation

/// Core morph operation: warp two images toward an interpolated shape, then
/// cross-dissolve the colors.
///
/// This is the direct Swift equivalent of `morph()` in the Python reference:
///
/// 1. Interpolate the two corresponding point sets to the mid-shape at time `t`.
/// 2. Delaunay-triangulate the mid-points.
/// 3. Inverse-warp each image to the mid-shape.
/// 4. Cross-dissolve the two warped images.
public enum Morpher {

    /// Morphs `img1` toward `img2` at time `t` (0...1).
    ///
    /// - Parameters:
    ///   - img1, img2: Source images of identical size.
    ///   - points1, points2: Corresponding feature points (landmarks + corners),
    ///     the same count and in the same order for both images.
    ///   - t: Interpolation parameter. `t == 0` reproduces `img1`, `t == 1`
    ///     reproduces `img2`.
    public static func morph(
        _ img1: ImageBuffer,
        _ img2: ImageBuffer,
        points1: [Point],
        points2: [Point],
        t: Double
    ) -> ImageBuffer {
        precondition(img1.width == img2.width && img1.height == img2.height, "images must be the same size")
        precondition(points1.count == points2.count, "point sets must correspond 1:1")
        precondition(points1.count >= 3, "need at least 3 points to triangulate")

        let mid = zip(points1, points2).map {
            Point((1 - t) * $0.0.x + t * $0.1.x, (1 - t) * $0.0.y + t * $0.1.y)
        }

        let triangles = Delaunay.triangulate(mid)

        let warped1 = AffineWarp.warp(source: img1, sourcePoints: points1, targetPoints: mid, triangles: triangles)
        let warped2 = AffineWarp.warp(source: img2, sourcePoints: points2, targetPoints: mid, triangles: triangles)

        return Dissolve.blend(warped1, warped2, t: t)
    }
}
