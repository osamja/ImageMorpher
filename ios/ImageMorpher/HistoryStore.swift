import Foundation
import UIKit

struct MorphRecord: Codable, Identifiable, Equatable {
    let id: UUID
    let createdAt: Date
    let videoFilename: String
    let thumbnailFilename: String
}

enum HistoryStoreError: Error {
    case thumbnailEncodingFailed
}

@MainActor
final class HistoryStore: ObservableObject {
    @Published private(set) var records: [MorphRecord] = []

    private let directory: URL
    private let recordsURL: URL

    init(directory: URL? = nil) {
        let base = directory ?? FileManager.default
            .urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("ImageMorpher", isDirectory: true)
        self.directory = base
        self.recordsURL = base.appendingPathComponent("history.json")
        try? FileManager.default.createDirectory(
            at: base,
            withIntermediateDirectories: true
        )
        load()
    }

    func save(videoURL: URL, thumbnail: UIImage) throws -> MorphRecord {
        let id = UUID()
        let videoFilename = "\(id.uuidString).mp4"
        let thumbnailFilename = "\(id.uuidString).png"
        let videoDestination = directory.appendingPathComponent(videoFilename)
        let thumbnailDestination = directory.appendingPathComponent(
            thumbnailFilename
        )

        try FileManager.default.copyItem(at: videoURL, to: videoDestination)
        guard let data = thumbnail.pngData() else {
            throw HistoryStoreError.thumbnailEncodingFailed
        }
        try data.write(to: thumbnailDestination, options: .atomic)

        let record = MorphRecord(
            id: id,
            createdAt: Date(),
            videoFilename: videoFilename,
            thumbnailFilename: thumbnailFilename
        )
        records.insert(record, at: 0)
        try persist()
        return record
    }

    func delete(_ record: MorphRecord) {
        try? FileManager.default.removeItem(at: videoURL(for: record))
        try? FileManager.default.removeItem(at: thumbnailURL(for: record))
        records.removeAll { $0.id == record.id }
        try? persist()
    }

    func videoURL(for record: MorphRecord) -> URL {
        directory.appendingPathComponent(record.videoFilename)
    }

    func thumbnailURL(for record: MorphRecord) -> URL {
        directory.appendingPathComponent(record.thumbnailFilename)
    }

    func thumbnail(for record: MorphRecord) -> UIImage? {
        UIImage(contentsOfFile: thumbnailURL(for: record).path)
    }

    private func load() {
        guard let data = try? Data(contentsOf: recordsURL),
              let saved = try? JSONDecoder().decode(
                  [MorphRecord].self,
                  from: data
              ) else {
            return
        }
        records = saved.sorted { $0.createdAt > $1.createdAt }
    }

    private func persist() throws {
        let data = try JSONEncoder().encode(records)
        try data.write(to: recordsURL, options: .atomic)
    }
}
