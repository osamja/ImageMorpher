import CoreGraphics
import Foundation
import ImageIO

public enum ImageLoaderError: Error, Equatable {
    case cannotDecode
    case cannotRender
    case invalidThumbnailSize(Int)
}

public enum ImageLoader {
    public static let defaultMaxPixelSize = 600

    public static func load(
        contentsOf url: URL,
        maxPixelSize: Int = defaultMaxPixelSize
    ) throws -> ImageBuffer {
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil) else {
            throw ImageLoaderError.cannotDecode
        }
        return try load(source: source, maxPixelSize: maxPixelSize)
    }

    public static func load(
        data: Data,
        maxPixelSize: Int = defaultMaxPixelSize
    ) throws -> ImageBuffer {
        guard let source = CGImageSourceCreateWithData(data as CFData, nil) else {
            throw ImageLoaderError.cannotDecode
        }
        return try load(source: source, maxPixelSize: maxPixelSize)
    }

    private static func load(source: CGImageSource, maxPixelSize: Int) throws -> ImageBuffer {
        guard maxPixelSize > 0 else {
            throw ImageLoaderError.invalidThumbnailSize(maxPixelSize)
        }
        let options: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceThumbnailMaxPixelSize: maxPixelSize,
            kCGImageSourceShouldCacheImmediately: true,
        ]
        guard let image = CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary) else {
            throw ImageLoaderError.cannotDecode
        }
        return try ImageBuffer(cgImage: image)
    }
}
