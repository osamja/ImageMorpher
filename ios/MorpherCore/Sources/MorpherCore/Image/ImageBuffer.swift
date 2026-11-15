import Foundation

public struct RGBA: Equatable, Hashable, Sendable {
    public var r: UInt8
    public var g: UInt8
    public var b: UInt8
    public var a: UInt8

    public init(r: UInt8, g: UInt8, b: UInt8, a: UInt8 = 255) {
        self.r = r
        self.g = g
        self.b = b
        self.a = a
    }

    public static let clear = RGBA(r: 0, g: 0, b: 0, a: 0)
    public static let black = RGBA(r: 0, g: 0, b: 0)
    public static let white = RGBA(r: 255, g: 255, b: 255)
}

public enum ImageBufferError: Error, Equatable {
    case invalidDimensions(width: Int, height: Int)
    case invalidPixelCount(expected: Int, actual: Int)
}

public struct ImageBuffer: Equatable, Sendable {
    public let width: Int
    public let height: Int
    public private(set) var pixels: [UInt8]

    public var bytesPerRow: Int { width * 4 }
    public var byteCount: Int { pixels.count }

    public init(width: Int, height: Int, pixels: [UInt8]) throws {
        guard width > 0, height > 0 else {
            throw ImageBufferError.invalidDimensions(width: width, height: height)
        }
        let expected = width * height * 4
        guard pixels.count == expected else {
            throw ImageBufferError.invalidPixelCount(expected: expected, actual: pixels.count)
        }
        self.width = width
        self.height = height
        self.pixels = pixels
    }

    public init(width: Int, height: Int, fill: RGBA = .clear) {
        precondition(width > 0 && height > 0, "ImageBuffer dimensions must be positive")
        self.width = width
        self.height = height
        var pixels = [UInt8](repeating: 0, count: width * height * 4)
        for offset in stride(from: 0, to: pixels.count, by: 4) {
            pixels[offset] = fill.r
            pixels[offset + 1] = fill.g
            pixels[offset + 2] = fill.b
            pixels[offset + 3] = fill.a
        }
        self.pixels = pixels
    }

    public func pixel(x: Int, y: Int) -> RGBA? {
        guard x >= 0, x < width, y >= 0, y < height else { return nil }
        let offset = (y * width + x) * 4
        return RGBA(
            r: pixels[offset],
            g: pixels[offset + 1],
            b: pixels[offset + 2],
            a: pixels[offset + 3]
        )
    }

    public mutating func setPixel(_ color: RGBA, x: Int, y: Int) {
        guard x >= 0, x < width, y >= 0, y < height else { return }
        let offset = (y * width + x) * 4
        pixels[offset] = color.r
        pixels[offset + 1] = color.g
        pixels[offset + 2] = color.b
        pixels[offset + 3] = color.a
    }

    public subscript(x: Int, y: Int) -> RGBA {
        get {
            guard let color = pixel(x: x, y: y) else {
                preconditionFailure("Pixel (\(x), \(y)) is outside \(width)x\(height)")
            }
            return color
        }
        set {
            setPixel(newValue, x: x, y: y)
        }
    }
}
