import Foundation
import simd

public struct TriangleVertices: Equatable, Sendable {
    public let a: SIMD2<Double>
    public let b: SIMD2<Double>
    public let c: SIMD2<Double>

    public init(a: SIMD2<Double>, b: SIMD2<Double>, c: SIMD2<Double>) {
        self.a = a
        self.b = b
        self.c = c
    }
}

public enum Barycentric {
    public static func coordinates(
        of point: SIMD2<Double>,
        in triangle: TriangleVertices
    ) -> SIMD3<Double>? {
        let v0 = triangle.b - triangle.a
        let v1 = triangle.c - triangle.a
        let v2 = point - triangle.a
        let denominator = cross(v0, v1)
        guard abs(denominator) > 1e-12 else { return nil }

        let beta = cross(v2, v1) / denominator
        let gamma = cross(v0, v2) / denominator
        let alpha = 1 - beta - gamma
        return SIMD3(alpha, beta, gamma)
    }

    public static func contains(
        _ point: SIMD2<Double>,
        in triangle: TriangleVertices,
        tolerance: Double = 0
    ) -> Bool {
        guard let weights = coordinates(of: point, in: triangle) else {
            return false
        }
        return weights.x >= -tolerance
            && weights.y >= -tolerance
            && weights.z >= -tolerance
    }

    public static func interpolate(
        _ weights: SIMD3<Double>,
        in triangle: TriangleVertices
    ) -> SIMD2<Double> {
        triangle.a * weights.x + triangle.b * weights.y + triangle.c * weights.z
    }

    private static func cross(_ lhs: SIMD2<Double>, _ rhs: SIMD2<Double>) -> Double {
        lhs.x * rhs.y - lhs.y * rhs.x
    }
}

public struct AffineMap {
    public let matrix: simd_double3x3

    public init(_ matrix: simd_double3x3) {
        self.matrix = matrix
    }

    public static func mapping(
        from source: TriangleVertices,
        to destination: TriangleVertices
    ) -> AffineMap? {
        let sourceMatrix = simd_double3x3(columns: (
            SIMD3(source.a.x, source.a.y, 1),
            SIMD3(source.b.x, source.b.y, 1),
            SIMD3(source.c.x, source.c.y, 1)
        ))
        let destinationMatrix = simd_double3x3(columns: (
            SIMD3(destination.a.x, destination.a.y, 1),
            SIMD3(destination.b.x, destination.b.y, 1),
            SIMD3(destination.c.x, destination.c.y, 1)
        ))
        guard abs(sourceMatrix.determinant) > 1e-12 else {
            return nil
        }
        return AffineMap(destinationMatrix * sourceMatrix.inverse)
    }

    public func apply(to point: SIMD2<Double>) -> SIMD2<Double> {
        let result = matrix * SIMD3(point.x, point.y, 1)
        return SIMD2(result.x / result.z, result.y / result.z)
    }

    public var inverted: AffineMap? {
        guard abs(matrix.determinant) > 1e-12 else {
            return nil
        }
        return AffineMap(matrix.inverse)
    }
}
