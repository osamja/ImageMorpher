import Foundation

/// A 2D point in continuous (Double) image coordinate space.
public struct Point: Hashable, Equatable, CustomStringConvertible {
    public var x: Double
    public var y: Double

    public init(_ x: Double, _ y: Double) {
        self.x = x
        self.y = y
    }

    public init(x: Double, y: Double) {
        self.x = x
        self.y = y
    }

    public var description: String { "(\(x), \(y))" }

    // MARK: - Vector arithmetic

    public static func + (lhs: Point, rhs: Point) -> Point {
        Point(lhs.x + rhs.x, lhs.y + rhs.y)
    }

    public static func - (lhs: Point, rhs: Point) -> Point {
        Point(lhs.x - rhs.x, lhs.y - rhs.y)
    }

    public static func * (lhs: Double, rhs: Point) -> Point {
        Point(lhs * rhs.x, lhs * rhs.y)
    }

    public static func * (lhs: Point, rhs: Double) -> Point {
        rhs * lhs
    }

    public static func dot(_ a: Point, _ b: Point) -> Double {
        a.x * b.x + a.y * b.y
    }

    public func distance(to other: Point) -> Double {
        let dx = x - other.x
        let dy = y - other.y
        return (dx * dx + dy * dy).squareRoot()
    }
}

/// Orientation of three points in the plane.
/// - Returns: > 0 if `a -> b -> c` is counter-clockwise, < 0 if clockwise, 0 if collinear.
public func orient2d(_ a: Point, _ b: Point, _ c: Point) -> Double {
    (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)
}
