import MorpherCore
import UIKit
import XCTest

@testable import ImageMorpher

@MainActor
final class MorphViewModelTests: XCTestCase {
    func testMorphPipelineProducesFramesVideoAndHistory() async throws {
        let directory = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
        try FileManager.default.createDirectory(
            at: directory,
            withIntermediateDirectories: true
        )
        defer {
            try? FileManager.default.removeItem(at: directory)
        }

        let historyStore = HistoryStore(directory: directory)
        let viewModel = MorphViewModel(historyStore: historyStore)
        defer {
            viewModel.pause()
            if let url = viewModel.videoURL {
                try? FileManager.default.removeItem(at: url)
            }
        }

        let size = 64
        let first = gradient(size: size, offset: 0)
        let second = gradient(size: size, offset: 40)
        let landmarks = syntheticLandmarks(width: size, height: size)
        let firstPreview = UIImage(
            cgImage: try XCTUnwrap(first.makeCGImage())
        )
        let secondPreview = UIImage(
            cgImage: try XCTUnwrap(second.makeCGImage())
        )

        viewModel.setPreparedImages(
            firstImage: first,
            firstLandmarks: landmarks,
            firstPreview: firstPreview,
            secondImage: second,
            secondLandmarks: landmarks,
            secondPreview: secondPreview
        )

        XCTAssertTrue(viewModel.canMorph)
        XCTAssertNil(viewModel.errorMessage)

        viewModel.morph()

        let deadline = Date().addingTimeInterval(60)
        while Date() < deadline {
            if let error = viewModel.errorMessage {
                XCTFail(error)
                return
            }
            if viewModel.videoURL != nil, !viewModel.historyRecords.isEmpty {
                break
            }
            try await Task.sleep(nanoseconds: 100_000_000)
        }

        XCTAssertEqual(viewModel.frames.count, 24)
        XCTAssertEqual(viewModel.historyRecords.count, 1)

        let videoURL = try XCTUnwrap(viewModel.videoURL)
        XCTAssertTrue(FileManager.default.fileExists(atPath: videoURL.path))
    }

    func testVisionFacePipelineWhenAvailable() async throws {
        let firstData = try fixtureData(named: "face-1")
        let secondData = try fixtureData(named: "face-2")

        do {
            for data in [firstData, secondData] {
                let image = try ImageLoader.load(data: data, maxPixelSize: 600)
                _ = try FaceCropper().crop(image)
            }
        } catch let error as FaceCropperError {
            if case .visionFailure = error {
                throw XCTSkip(
                    "Vision is unavailable in this environment: \(error)"
                )
            }
            throw error
        }

        let directory = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
        try FileManager.default.createDirectory(
            at: directory,
            withIntermediateDirectories: true
        )
        defer {
            try? FileManager.default.removeItem(at: directory)
        }

        let viewModel = MorphViewModel(
            historyStore: HistoryStore(directory: directory)
        )
        await viewModel.setImageData(firstData, for: .first)
        await viewModel.setImageData(secondData, for: .second)

        XCTAssertTrue(viewModel.canMorph)
        XCTAssertNil(viewModel.errorMessage)
    }

    private func gradient(size: Int, offset: Int) -> ImageBuffer {
        var image = ImageBuffer(width: size, height: size, fill: .black)
        for y in 0..<size {
            for x in 0..<size {
                image[x, y] = RGBA(
                    r: UInt8((x * 4 + offset) % 256),
                    g: UInt8((y * 4 + offset * 2) % 256),
                    b: 120
                )
            }
        }
        return image
    }

    private func syntheticLandmarks(width: Int, height: Int) -> Landmarks {
        let width = Double(width)
        let height = Double(height)
        var points: [SIMD2<Double>] = []
        points.reserveCapacity(68)

        for row in 0..<4 {
            for column in 0..<17 {
                let jitter = Double((row * 17 + column) % 3) * 0.25
                points.append(
                    SIMD2(
                        width * Double(column + 1) / 18 + jitter,
                        height * Double(row + 1) / 5 + jitter
                    )
                )
            }
        }
        return Landmarks(points: points)
    }

    private func fixtureData(named name: String) throws -> Data {
        let bundle = Bundle(for: Self.self)
        let url = try XCTUnwrap(
            bundle.url(forResource: name, withExtension: "jpeg")
        )
        return try Data(contentsOf: url)
    }
}
