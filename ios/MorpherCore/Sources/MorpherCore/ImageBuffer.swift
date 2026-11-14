import Foundation

/// An RGBA8 image buffer stored row-major (top-left origin), 4 bytes per pixel.
///
/// This is the platform-agnostic pixel representation used throughout the morph
/// pipeline. On Apple platforms it can be converted to/from `CGImage`; on Linux
/// it can be read/written as PPM via `PPMImage`.
public struct ImageBuffer {
    public var width: Int
    public var height: Int
    /// RGBA bytes, length == width * height * 4, row-major.
    public var pixels: [UInt8]

    public init(width: Int, height: Int, pixels: [UInt8]? = nil) {
        self.width = width
        self.height = height
        if let pixels {
            precondition(pixels.count == width * height * 4, "RGBA buffer size mismatch")
            self.pixels = pixels
        } else {
            self.pixels = [UInt8](repeating: 0, count: width * height * 4)
        }
    }

    /// Creates a solid-color image.
    public init(width: Int, height: Int, color: (r: UInt8, g: UInt8, b: UInt8)) {
        self.init(width: width, height: height)
        for y in 0..<height {
            for x in 0..<width {
                setPixel(x: x, y: y, r: color.r, g: color.g, b: color.b)
            }
        }
    }

    @inline(__always)
    public func index(_ x: Int, _ y: Int) -> Int {
        (y * width + x) * 4
    }

    public func pixel(x: Int, y: Int) -> (r: UInt8, g: UInt8, b: UInt8, a: UInt8) {
        let i = index(x, y)
        return (pixels[i], pixels[i + 1], pixels[i + 2], pixels[i + 3])
    }

    public mutating func setPixel(x: Int, y: Int, r: UInt8, g: UInt8, b: UInt8, a: UInt8 = 255) {
        let i = index(x, y)
        pixels[i] = r
        pixels[i + 1] = g
        pixels[i + 2] = b
        pixels[i + 3] = a
    }

    /// Samples the image at continuous coordinates using nearest-neighbor
    /// with clamping to the image bounds.
    public func sampleNearest(_ px: Double, _ py: Double) -> (r: UInt8, g: UInt8, b: UInt8, a: UInt8) {
        let x = min(max(Int(px.rounded(.down)), 0), width - 1)
        let y = min(max(Int(py.rounded(.down)), 0), height - 1)
        return pixel(x: x, y: y)
    }

    /// Samples the image at continuous coordinates using bilinear interpolation
    /// with clamping to the image bounds.
    public func sampleBilinear(_ px: Double, _ py: Double) -> (r: UInt8, g: UInt8, b: UInt8, a: UInt8) {
        let cx = min(max(px, 0), Double(width - 1))
        let cy = min(max(py, 0), Double(height - 1))
        let x0 = Int(cx.rounded(.down))
        let y0 = Int(cy.rounded(.down))
        let x1 = min(x0 + 1, width - 1)
        let y1 = min(y0 + 1, height - 1)
        let fx = cx - Double(x0)
        let fy = cy - Double(y0)

        let p00 = pixel(x: x0, y: y0)
        let p10 = pixel(x: x1, y: y0)
        let p01 = pixel(x: x0, y: y1)
        let p11 = pixel(x: x1, y: y1)

        func lerp(_ a: UInt8, _ b: UInt8, _ t: Double) -> UInt8 {
            UInt8((Double(a) * (1 - t) + Double(b) * t).rounded())
        }

        let top = (lerp(p00.r, p10.r, fx), lerp(p00.g, p10.g, fx), lerp(p00.b, p10.b, fx), lerp(p00.a, p10.a, fx))
        let bottom = (lerp(p01.r, p11.r, fx), lerp(p01.g, p11.g, fx), lerp(p01.b, p11.b, fx), lerp(p01.a, p11.a, fx))
        return (lerp(top.0, bottom.0, fy), lerp(top.1, bottom.1, fy), lerp(top.2, bottom.2, fy), lerp(top.3, bottom.3, fy))
    }
}
