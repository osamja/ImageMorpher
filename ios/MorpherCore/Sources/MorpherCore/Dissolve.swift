import Foundation

/// Cross-dissolve of two equally-sized images: `(1 - t) * a + t * b`.
public enum Dissolve {

    public static func blend(_ a: ImageBuffer, _ b: ImageBuffer, t: Double) -> ImageBuffer {
        precondition(a.width == b.width && a.height == b.height, "images must be the same size")

        var out = ImageBuffer(width: a.width, height: a.height)
        let n = a.width * a.height * 4
        for i in 0..<n {
            let value = (1 - t) * Double(a.pixels[i]) + t * Double(b.pixels[i])
            out.pixels[i] = UInt8(value.rounded())
        }
        return out
    }
}
