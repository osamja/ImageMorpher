import CoreGraphics
import Foundation
import ImageIO
import UniformTypeIdentifiers

public enum StillExporterError: Error, Equatable {
    case renderingFailed
    case encodingFailed
}

public enum StillExporter {
    public static func cgImage(from buffer: ImageBuffer) throws -> CGImage {
        guard let image = buffer.makeCGImage() else {
            throw StillExporterError.renderingFailed
        }
        return image
    }

    public static func pngData(from buffer: ImageBuffer) throws -> Data {
        let image = try cgImage(from: buffer)
        let data = NSMutableData()
        guard let destination = CGImageDestinationCreateWithData(
            data,
            UTType.png.identifier as CFString,
            1,
            nil
        ) else {
            throw StillExporterError.encodingFailed
        }
        CGImageDestinationAddImage(destination, image, nil)
        guard CGImageDestinationFinalize(destination) else {
            throw StillExporterError.encodingFailed
        }
        return data as Data
    }

    public static func writePNG(_ buffer: ImageBuffer, to url: URL) throws {
        try pngData(from: buffer).write(to: url, options: .atomic)
    }
}
