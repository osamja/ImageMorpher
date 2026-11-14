import Foundation

/// A triangle referencing three point indices.
public struct Triangle: Hashable, Equatable {
    public var a: Int
    public var b: Int
    public var c: Int

    public init(_ a: Int, _ b: Int, _ c: Int) {
        self.a = a
        self.b = b
        self.c = c
    }
}

/// An undirected edge between two point indices (order-independent).
struct Edge: Hashable {
    let a: Int
    let b: Int

    init(_ a: Int, _ b: Int) {
        self.a = min(a, b)
        self.b = max(a, b)
    }
}

/// Bowyer–Watson Delaunay triangulation over a set of 2D points.
///
/// This is a pure-Swift replacement for `scipy.spatial.Delaunay`. The point
/// counts involved (~70 face landmarks + corners) are small, so the simple
/// O(n^2) Bowyer–Watson algorithm is more than adequate.
public enum Delaunay {

    public static func triangulate(_ points: [Point]) -> [Triangle] {
        guard points.count >= 3 else { return [] }

        // Super-triangle large enough to contain every point.
        var minX = Double.greatestFiniteMagnitude
        var minY = Double.greatestFiniteMagnitude
        var maxX = -Double.greatestFiniteMagnitude
        var maxY = -Double.greatestFiniteMagnitude
        for p in points {
            minX = min(minX, p.x); minY = min(minY, p.y)
            maxX = max(maxX, p.x); maxY = max(maxY, p.y)
        }
        let dmax = max(maxX - minX, maxY - minY, 1.0)
        let midX = (minX + maxX) / 2
        let midY = (minY + maxY) / 2
        let s0 = Point(midX - 20 * dmax, midY - dmax)
        let s1 = Point(midX, midY + 20 * dmax)
        let s2 = Point(midX + 20 * dmax, midY - dmax)

        var pts = points
        pts.append(contentsOf: [s0, s1, s2])
        let superA = points.count
        let superB = points.count + 1
        let superC = points.count + 2

        var triangles = [Triangle(superA, superB, superC)]

        for i in 0..<points.count {
            let p = pts[i]

            // 1. Find all triangles whose circumcircle contains p.
            var bad: [Triangle] = []
            for t in triangles where inCircumcircle(pts[t.a], pts[t.b], pts[t.c], p) {
                bad.append(t)
            }
            guard !bad.isEmpty else { continue }

            // 2. Boundary of the polygonal hole = edges not shared by two bad triangles.
            var polygon: [Edge] = []
            for t in bad {
                for e in edges(of: t) {
                    let shared = bad.contains { other in
                        other != t && edges(of: other).contains(e)
                    }
                    if !shared { polygon.append(e) }
                }
            }

            // 3. Remove bad triangles.
            triangles.removeAll { bad.contains($0) }

            // 4. Re-triangulate the hole using p.
            for e in polygon {
                triangles.append(Triangle(e.a, e.b, i))
            }
        }

        // Drop any triangle touching the super-triangle vertices.
        let superSet: Set<Int> = [superA, superB, superC]
        return triangles.filter { t in
            !superSet.contains(t.a) && !superSet.contains(t.b) && !superSet.contains(t.c)
        }
    }

    /// True if `p` is strictly inside the circumcircle of triangle (a, b, c).
    /// Orientation-independent.
    static func inCircumcircle(_ a: Point, _ b: Point, _ c: Point, _ p: Point) -> Bool {
        let ax = a.x - p.x, ay = a.y - p.y
        let bx = b.x - p.x, by = b.y - p.y
        let cx = c.x - p.x, cy = c.y - p.y
        let det = (ax * ax + ay * ay) * (bx * cy - by * cx)
                - (bx * bx + by * by) * (ax * cy - ay * cx)
                + (cx * cx + cy * cy) * (ax * by - ay * bx)
        let orient = (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)
        return det * orient > 0
    }

    static func edges(of t: Triangle) -> [Edge] {
        [Edge(t.a, t.b), Edge(t.b, t.c), Edge(t.c, t.a)]
    }
}
