import UIKit
import XCTest

@testable import ImageMorpher

@MainActor
final class HistoryStoreTests: XCTestCase {
    func testSaveReloadAndDelete() throws {
        let directory = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
        try FileManager.default.createDirectory(
            at: directory,
            withIntermediateDirectories: true
        )
        defer {
            try? FileManager.default.removeItem(at: directory)
        }

        let sourceVideo = directory.appendingPathComponent("source.mp4")
        try Data([0, 1, 2, 3]).write(to: sourceVideo)

        let renderer = UIGraphicsImageRenderer(
            size: CGSize(width: 1, height: 1)
        )
        let thumbnail = renderer.image { context in
            UIColor.red.setFill()
            context.fill(CGRect(x: 0, y: 0, width: 1, height: 1))
        }

        let store = HistoryStore(directory: directory)
        let record = try store.save(
            videoURL: sourceVideo,
            thumbnail: thumbnail
        )

        XCTAssertEqual(store.records.count, 1)
        XCTAssertTrue(
            FileManager.default.fileExists(
                atPath: store.videoURL(for: record).path
            )
        )
        XCTAssertTrue(
            FileManager.default.fileExists(
                atPath: store.thumbnailURL(for: record).path
            )
        )
        XCTAssertNotNil(store.thumbnail(for: record))

        let reloaded = HistoryStore(directory: directory)
        XCTAssertEqual(reloaded.records, store.records)

        reloaded.delete(record)
        XCTAssertTrue(reloaded.records.isEmpty)
        XCTAssertFalse(
            FileManager.default.fileExists(
                atPath: reloaded.videoURL(for: record).path
            )
        )
    }
}
