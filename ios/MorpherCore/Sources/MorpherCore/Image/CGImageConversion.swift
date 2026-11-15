import CoreGraphics
import Foundation

extension ImageBuffer {
    init(cgImage: CGImage) throws {
        let width = cgImage.width
        let height = cgImage.height
        guard width > 0, height > 0 else {
            throw ImageLoaderError.cannotRender
        }
        let bytesPerRow = width * 4
        guard let context = CGContext(
            data: nil,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: bytesPerRow,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            throw ImageLoaderError.cannotRender
        }
        context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))
        guard let data = context.data else {
            throw ImageLoaderError.cannotRender
        }
        let buffer = data.bindMemory(to: UInt8.self, capacity: bytesPerRow * height)
        let pixels = Array(UnsafeBufferPointer(start: buffer, count: bytesPerRow * height))
        try self.init(width: width, height: height, pixels: pixels)
    }

    public func makeCGImage() -> CGImage? {
        guard let provider = CGDataProvider(data: Data(pixels) as CFData) else {
            return nil
        }
        return CGImage(
            width: width,
            height: height,
            bitsPerComponent: 8,
            bitsPerPixel: 32,
            bytesPerRow: bytesPerRow,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue),
            provider: provider,
            decode: nil,
            shouldInterpolate: true,
            intent: .defaultIntent
        )
    }
}
