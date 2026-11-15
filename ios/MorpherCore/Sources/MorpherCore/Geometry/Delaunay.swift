import Foundation

public enum Delaunay {
    public static func triangulate(_ points: [SIMD2<Double>]) -> [Triangle] {
        var uniquePoints: [SIMD2<Double>] = []
        var sourceIndices: [Int] = []
        var seen: [SIMD2<Double>: Int] = [:]

        for (index, point) in points.enumerated() where point.x.isFinite && point.y.isFinite {
            guard seen[point] == nil else { continue }
            seen[point] = uniquePoints.count
            uniquePoints.append(point)
            sourceIndices.append(index)
        }

        guard uniquePoints.count >= 3, !isCollinear(uniquePoints) else {
            return []
        }

        var factor = 100.0
        var lastCandidate: [IndexTriangle] = []
        for _ in 0..<6 {
            let candidate = bowyerWatson(uniquePoints, marginFactor: factor)
            let realTriangles = candidate.filter {
                $0.a < uniquePoints.count
                    && $0.b < uniquePoints.count
                    && $0.c < uniquePoints.count
            }
            lastCandidate = realTriangles
            if isValid(realTriangles, points: uniquePoints) {
                return finalize(realTriangles, sourceIndices: sourceIndices)
            }
            factor *= 100
        }

        return finalize(lastCandidate, sourceIndices: sourceIndices)
    }

    static func orientation(
        _ a: SIMD2<Double>,
        _ b: SIMD2<Double>,
        _ c: SIMD2<Double>
    ) -> Double {
        let left = (a.x - c.x) * (b.y - c.y)
        let right = (a.y - c.y) * (b.x - c.x)
        let determinant = left - right
        let bound = 3.3306690738754716e-16 * (abs(left) + abs(right))
        guard abs(determinant) <= bound else {
            return determinant
        }
        let exact = decimalOrientation(a, b, c)
        if exact > 0 {
            return .leastNonzeroMagnitude
        }
        if exact < 0 {
            return -.leastNonzeroMagnitude
        }
        return 0
    }

    private static func bowyerWatson(
        _ points: [SIMD2<Double>],
        marginFactor: Double
    ) -> [IndexTriangle] {
        var minX = points[0].x
        var maxX = minX
        var minY = points[0].y
        var maxY = minY
        for point in points.dropFirst() {
            minX = min(minX, point.x)
            maxX = max(maxX, point.x)
            minY = min(minY, point.y)
            maxY = max(maxY, point.y)
        }

        let midX = (minX + maxX) / 2
        let midY = (minY + maxY) / 2
        let span = max(maxX - minX, maxY - minY)
        let margin = span > 0 ? span * marginFactor : 10

        let superStart = points.count
        var vertices = points
        vertices.append(SIMD2(midX - 3 * margin, midY - margin))
        vertices.append(SIMD2(midX + 3 * margin, midY - margin))
        vertices.append(SIMD2(midX, midY + 3 * margin))

        var triangles = [
            IndexTriangle(superStart, superStart + 1, superStart + 2, vertices: vertices),
        ]

        for pointIndex in points.indices {
            let point = vertices[pointIndex]
            var kept: [IndexTriangle] = []
            var cavity: [IndexTriangle] = []
            kept.reserveCapacity(triangles.count)

            for triangle in triangles {
                if isInCircumcircle(point, triangle, vertices: vertices) {
                    cavity.append(triangle)
                } else {
                    kept.append(triangle)
                }
            }

            guard !cavity.isEmpty else { continue }

            var edgeCounts: [Edge: Int] = [:]
            for triangle in cavity {
                edgeCounts[Edge(triangle.a, triangle.b), default: 0] += 1
                edgeCounts[Edge(triangle.b, triangle.c), default: 0] += 1
                edgeCounts[Edge(triangle.c, triangle.a), default: 0] += 1
            }

            for (edge, count) in edgeCounts {
                guard count == 1, edgeCounts[Edge(edge.v, edge.u)] == nil else {
                    continue
                }
                let triangle = IndexTriangle(edge.u, edge.v, pointIndex, vertices: vertices)
                if !triangle.isDegenerate {
                    kept.append(triangle)
                }
            }

            triangles = kept
        }

        return triangles
    }

    private static func isValid(
        _ triangles: [IndexTriangle],
        points: [SIMD2<Double>]
    ) -> Bool {
        guard !triangles.isEmpty else { return false }

        var used: Set<Int> = []
        var triangleArea = 0.0
        for triangle in triangles {
            used.insert(triangle.a)
            used.insert(triangle.b)
            used.insert(triangle.c)
            triangleArea += abs(
                orientation(points[triangle.a], points[triangle.b], points[triangle.c])
            ) / 2
        }
        guard used.count == points.count else { return false }

        let hullArea = convexHullArea(points)
        guard abs(triangleArea - hullArea) <= max(1, hullArea) * 1e-9 else {
            return false
        }

        for triangle in triangles {
            for index in points.indices
            where index != triangle.a && index != triangle.b && index != triangle.c {
                if isInCircumcircle(points[index], triangle, vertices: points) {
                    return false
                }
            }
        }

        return true
    }

    private static func finalize(
        _ triangles: [IndexTriangle],
        sourceIndices: [Int]
    ) -> [Triangle] {
        var result: [Triangle] = []
        result.reserveCapacity(triangles.count)
        for triangle in triangles where !triangle.isDegenerate {
            result.append(
                Triangle(
                    sourceIndices[triangle.a],
                    sourceIndices[triangle.b],
                    sourceIndices[triangle.c]
                )
            )
        }
        return result.sorted {
            $0.sortedIndices.lexicographicallyPrecedes($1.sortedIndices)
        }
    }

    private static func convexHullArea(_ points: [SIMD2<Double>]) -> Double {
        let sorted = points.sorted {
            $0.x < $1.x || ($0.x == $1.x && $0.y < $1.y)
        }

        var lower: [SIMD2<Double>] = []
        for point in sorted {
            while lower.count >= 2,
                  orientation(lower[lower.count - 2], lower[lower.count - 1], point) <= 0 {
                lower.removeLast()
            }
            lower.append(point)
        }

        var upper: [SIMD2<Double>] = []
        for point in sorted.reversed() {
            while upper.count >= 2,
                  orientation(upper[upper.count - 2], upper[upper.count - 1], point) <= 0 {
                upper.removeLast()
            }
            upper.append(point)
        }

        lower.removeLast()
        upper.removeLast()
        let hull = lower + upper
        guard hull.count >= 3 else { return 0 }

        var twiceArea = 0.0
        for index in hull.indices {
            let a = hull[index]
            let b = hull[(index + 1) % hull.count]
            twiceArea += a.x * b.y - b.x * a.y
        }
        return abs(twiceArea) / 2
    }

    private static func isCollinear(_ points: [SIMD2<Double>]) -> Bool {
        let first = points[0]
        guard let second = points.dropFirst().first(where: { $0 != first }) else {
            return true
        }
        return points.allSatisfy { orientation(first, second, $0) == 0 }
    }

    private static func isInCircumcircle(
        _ point: SIMD2<Double>,
        _ triangle: IndexTriangle,
        vertices: [SIMD2<Double>]
    ) -> Bool {
        let a = vertices[triangle.a]
        let b = vertices[triangle.b]
        let c = vertices[triangle.c]

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

        let determinant = alift * bcdet + blift * cadet + clift * abdet
        let permanent = (abs(bdx * cdy) + abs(cdx * bdy)) * alift
            + (abs(cdx * ady) + abs(adx * cdy)) * blift
            + (abs(adx * bdy) + abs(bdx * ady)) * clift
        let bound = 2.220446049250313e-15 * permanent
        guard abs(determinant) <= bound else {
            return determinant > 0
        }
        return decimalInCircle(point, a, b, c) > 0
    }

    private static func decimalOrientation(
        _ a: SIMD2<Double>,
        _ b: SIMD2<Double>,
        _ c: SIMD2<Double>
    ) -> Decimal {
        (Decimal(a.x) - Decimal(c.x)) * (Decimal(b.y) - Decimal(c.y))
            - (Decimal(a.y) - Decimal(c.y)) * (Decimal(b.x) - Decimal(c.x))
    }

    private static func decimalInCircle(
        _ point: SIMD2<Double>,
        _ a: SIMD2<Double>,
        _ b: SIMD2<Double>,
        _ c: SIMD2<Double>
    ) -> Decimal {
        let adx = Decimal(a.x) - Decimal(point.x)
        let ady = Decimal(a.y) - Decimal(point.y)
        let bdx = Decimal(b.x) - Decimal(point.x)
        let bdy = Decimal(b.y) - Decimal(point.y)
        let cdx = Decimal(c.x) - Decimal(point.x)
        let cdy = Decimal(c.y) - Decimal(point.y)

        let abdet = adx * bdy - bdx * ady
        let bcdet = bdx * cdy - cdx * bdy
        let cadet = cdx * ady - adx * cdy
        let alift = adx * adx + ady * ady
        let blift = bdx * bdx + bdy * bdy
        let clift = cdx * cdx + cdy * cdy

        return alift * bcdet + blift * cadet + clift * abdet
    }
}

private struct Edge: Hashable {
    let u: Int
    let v: Int

    init(_ u: Int, _ v: Int) {
        self.u = u
        self.v = v
    }
}

private struct IndexTriangle {
    let a: Int
    let b: Int
    let c: Int
    let isDegenerate: Bool

    init(_ a: Int, _ b: Int, _ c: Int, vertices: [SIMD2<Double>]) {
        let orientation = Delaunay.orientation(vertices[a], vertices[b], vertices[c])
        if orientation < 0 {
            self.a = a
            self.b = c
            self.c = b
        } else {
            self.a = a
            self.b = b
            self.c = c
        }
        self.isDegenerate = orientation == 0
    }
}
