import AVFoundation
import XCTest

@testable import MorpherCore

final class VideoEncoderTests: XCTestCase {
    func testEncodesFramesToPlayableVideo() async throws {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathExtension("mp4")
        defer {
            try? FileManager.default.removeItem(at: url)
        }

        let encoder = try VideoEncoder(
            url: url,
            width: 64,
            height: 48,
            options: VideoEncoderOptions(codec: .h264, frameRate: 10)
        )
        for index in 0..<3 {
            var image = TestSupport.gradientImage(width: 64, height: 48)
            for y in 0..<48 {
                for x in 0..<64 {
                    let color = image[x, y]
                    image[x, y] = RGBA(
                        r: color.r &+ UInt8(index * 20),
                        g: color.g,
                        b: color.b,
                        a: color.a
                    )
                }
            }
            try encoder.append(image)
        }
        try await encoder.finish()

        XCTAssertTrue(FileManager.default.fileExists(atPath: url.path))
        let attributes = try FileManager.default.attributesOfItem(
            atPath: url.path
        )
        XCTAssertGreaterThan((attributes[.size] as? Int) ?? 0, 0)

        let asset = AVURLAsset(url: url)
        let duration = try await asset.load(.duration)
        XCTAssertEqual(duration.seconds, 0.3, accuracy: 0.08)
        let tracks = try await asset.loadTracks(withMediaType: .video)
        let track = try XCTUnwrap(tracks.first)
        let naturalSize = try await track.load(.naturalSize)
        XCTAssertEqual(naturalSize.width, 64)
        XCTAssertEqual(naturalSize.height, 48)
    }

    func testRejectsOddDimensions() {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathExtension("mp4")

        XCTAssertThrowsError(
            try VideoEncoder(url: url, width: 63, height: 48)
        ) { error in
            XCTAssertEqual(
                error as? VideoEncoderError,
                .invalidDimensions(width: 63, height: 48)
            )
        }
    }

    func testRejectsFrameSizeMismatch() throws {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathExtension("mp4")
        defer {
            try? FileManager.default.removeItem(at: url)
        }

        let encoder = try VideoEncoder(url: url, width: 64, height: 48)
        defer { encoder.cancel() }

        XCTAssertThrowsError(
            try encoder.append(
                TestSupport.solidImage(width: 32, height: 32, color: .black)
            )
        ) { error in
            XCTAssertEqual(error as? VideoEncoderError, .imageSizeMismatch)
        }
    }
}
