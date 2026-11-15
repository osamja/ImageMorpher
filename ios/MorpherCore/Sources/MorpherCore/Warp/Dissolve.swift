import Foundation

public enum Dissolve {
    public static func blend(
        _ first: ImageBuffer,
        _ second: ImageBuffer,
        t: Double
    ) throws -> ImageBuffer {
        guard first.width == second.width, first.height == second.height else {
            throw MorpherError.imageSizeMismatch
        }

        var pixels = [UInt8](repeating: 0, count: first.byteCount)
        let firstWeight = 1 - t
        let secondWeight = t

        for offset in stride(from: 0, to: pixels.count, by: 4) {
            for channel in 0..<4 {
                let firstValue = Int(firstWeight * Double(first.pixels[offset + channel]))
                let secondValue = Int(secondWeight * Double(second.pixels[offset + channel]))
                pixels[offset + channel] = UInt8(
                    min(255, max(0, firstValue + secondValue))
                )
            }
        }

        return try ImageBuffer(
            width: first.width,
            height: first.height,
            pixels: pixels
        )
    }
}
