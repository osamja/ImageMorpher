import Foundation

/// Barycentric coordinate helpers for point-in-triangle tests and affine mapping.
public enum Barycentric {

    /// Barycentric coordinates (u, v, w) of `p` relative to triangle (a, b, c),
    /// such that `p = u*a + v*b + w*c` and `u + v + w == 1`.
    public static func coordinates(_ p: Point, _ a: Point, _ b: Point, _ c: Point) -> (u: Double, v: Double, w: Double) {
        let v0 = b - a
        let v1 = c - a
        let v2 = p - a
        let d00 = Point.dot(v0, v0)
        let d01 = Point.dot(v0, v1)
        let d11 = Point.dot(v1, v1)
        let d20 = Point.dot(v2, v0)
        let d21 = Point.dot(v2, v1)
        let denom = d00 * d11 - d01 * d01
        guard abs(denom) > 1e-15 else { return (0, 0, 0) }
        let v = (d11 * d20 - d01 * d21) / denom
        let w = (d00 * d21 - d01 * d20) / denom
        let u = 1 - v - w
        return (u, v, w)
    }

    /// True if the barycentric coordinates place `p` inside (or on the boundary of)
    /// the triangle, within a small tolerance.
    public static func isInside(_ bc: (u: Double, v: Double, w: Double), epsilon: Double = 1e-9) -> Bool {
        bc.u >= -epsilon && bc.v >= -epsilon && bc.w >= -epsilon
    }
}
