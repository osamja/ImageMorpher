import Foundation

public struct Triangle: Hashable, Sendable {
    public let a: Int
    public let b: Int
    public let c: Int

    public init(_ a: Int, _ b: Int, _ c: Int) {
        precondition(a != b && b != c && a != c, "Triangle vertices must be distinct")
        self.a = a
        self.b = b
        self.c = c
    }

    public var indices: [Int] { [a, b, c] }

    public var sortedIndices: [Int] { indices.sorted() }
}
