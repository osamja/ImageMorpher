import CoreGraphics
import Foundation
import ImageIO
import MorpherCore
import UniformTypeIdentifiers
import XCTest

enum TestSupport {
    static var repoRoot: URL {
        URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
    }

    static func inputImage(_ name: String) -> URL {
        repoRoot
            .appendingPathComponent("imagemorpher/morph/tests/content/input")
            .appendingPathComponent(name)
    }

    static func fixtureURL(named name: String) throws -> URL {
        try XCTUnwrap(
            Bundle.module.url(
                forResource: name,
                withExtension: "json",
                subdirectory: "Fixtures"
            )
        )
    }

    static func makeColorfulCGImage() throws -> CGImage {
        let bytes: [UInt8] = [
            255, 0, 0, 255, 0, 255, 0, 255,
            0, 0, 255, 255, 255, 255, 255, 255,
        ]
        let provider = try XCTUnwrap(CGDataProvider(data: Data(bytes) as CFData))
        return try XCTUnwrap(
            CGImage(
                width: 2,
                height: 2,
                bitsPerComponent: 8,
                bitsPerPixel: 32,
                bytesPerRow: 8,
                space: CGColorSpaceCreateDeviceRGB(),
                bitmapInfo: CGBitmapInfo(
                    rawValue: CGImageAlphaInfo.premultipliedLast.rawValue
                ),
                provider: provider,
                decode: nil,
                shouldInterpolate: false,
                intent: .defaultIntent
            )
        )
    }

    static func gradientImage(width: Int, height: Int) -> ImageBuffer {
        var image = ImageBuffer(width: width, height: height)
        for y in 0..<height {
            for x in 0..<width {
                image[x, y] = RGBA(
                    r: UInt8((x * 7) % 256),
                    g: UInt8((y * 11) % 256),
                    b: UInt8(((x + y) * 5) % 256)
                )
            }
        }
        return image
    }

    static func solidImage(
        width: Int,
        height: Int,
        color: RGBA
    ) -> ImageBuffer {
        ImageBuffer(width: width, height: height, fill: color)
    }

    static func gridPoints(
        width: Int,
        height: Int,
        columns: Int,
        rows: Int
    ) -> [SIMD2<Double>] {
        let width = Double(width)
        let height = Double(height)
        var points = [
            SIMD2<Double>(0, 0),
            SIMD2<Double>(0, height),
            SIMD2<Double>(width, 0),
            SIMD2<Double>(width, height),
        ]
        for row in 0..<rows {
            for column in 0..<columns {
                points.append(
                    SIMD2(
                        width * Double(column + 1) / Double(columns + 1),
                        height * Double(row + 1) / Double(rows + 1)
                    )
                )
            }
        }
        return points
    }

    static func pngData(for image: CGImage) throws -> Data {
        let data = NSMutableData()
        let destination = try XCTUnwrap(
            CGImageDestinationCreateWithData(
                data,
                UTType.png.identifier as CFString,
                1,
                nil
            )
        )
        CGImageDestinationAddImage(destination, image, nil)
        XCTAssertTrue(CGImageDestinationFinalize(destination))
        return data as Data
    }
}
