import Foundation

/// Per-triangle piecewise-affine inverse warp.
///
/// Maps each output pixel (in the target triangulation) back through the
/// corresponding source triangle via barycentric coordinates, then samples the
/// source image. This mirrors the numpy inverse-transform warp in the Python
/// reference (`getInverseTransformation` + `getWarpedImg`).
public enum AffineWarp {

    public static func warp(
        source: ImageBuffer,
        sourcePoints: [Point],
        targetPoints: [Point],
        triangles: [Triangle]
    ) -> ImageBuffer {
        precondition(sourcePoints.count == targetPoints.count, "point sets must correspond 1:1")

        var out = ImageBuffer(width: source.width, height: source.height)

        for tri in triangles {
            let ta = targetPoints[tri.a]
            let tb = targetPoints[tri.b]
            let tc = targetPoints[tri.c]
            let sa = sourcePoints[tri.a]
            let sb = sourcePoints[tri.b]
            let sc = sourcePoints[tri.c]

            // Axis-aligned bounding box of the target triangle, clamped to the image.
            let minX = max(0, Int(floor(min(ta.x, tb.x, tc.x))))
            let maxX = min(source.width - 1, Int(ceil(max(ta.x, tb.x, tc.x))))
            let minY = max(0, Int(floor(min(ta.y, tb.y, tc.y))))
            let maxY = min(source.height - 1, Int(ceil(max(ta.y, tb.y, tc.y))))
            guard minX <= maxX, minY <= maxY else { continue }

            for y in minY...maxY {
                for x in minX...maxX {
                    let p = Point(Double(x), Double(y))
                    let bc = Barycentric.coordinates(p, ta, tb, tc)
                    guard Barycentric.isInside(bc) else { continue }
                    let qx = bc.u * sa.x + bc.v * sb.x + bc.w * sc.x
                    let qy = bc.u * sa.y + bc.v * sb.y + bc.w * sc.y
                    let c = source.sampleBilinear(qx, qy)
                    out.setPixel(x: x, y: y, r: c.r, g: c.g, b: c.b, a: c.a)
                }
            }
        }
        return out
    }
}
