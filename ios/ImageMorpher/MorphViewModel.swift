import Foundation
import MorpherCore
import Photos
import UIKit

@MainActor
final class MorphViewModel: ObservableObject {
    enum Slot {
        case first
        case second
    }

    enum Stage: Equatable {
        case empty
        case loading
        case ready
        case processing(completed: Int, total: Int)
        case finished
    }

    @Published private(set) var stage: Stage = .empty
    @Published private(set) var firstPreview: UIImage?
    @Published private(set) var secondPreview: UIImage?
    @Published private(set) var frames: [UIImage] = []
    @Published private(set) var currentFrameIndex = 0
    @Published private(set) var isPlaying = false
    @Published private(set) var videoURL: URL?
    @Published private(set) var savedToPhotos = false
    @Published private(set) var historyRecords: [MorphRecord] = []
    @Published var errorMessage: String?

    private let historyStore: HistoryStore
    private var firstImage: ImageBuffer?
    private var secondImage: ImageBuffer?
    private var firstLandmarks: Landmarks?
    private var secondLandmarks: Landmarks?
    private var playbackTask: Task<Void, Never>?
    private var morphTask: Task<Void, Never>?

    init(historyStore: HistoryStore? = nil) {
        let store = historyStore ?? HistoryStore()
        self.historyStore = store
        self.historyRecords = store.records
    }

    var canMorph: Bool {
        firstImage != nil
            && secondImage != nil
            && firstLandmarks != nil
            && secondLandmarks != nil
    }

    var currentFrame: UIImage? {
        guard frames.indices.contains(currentFrameIndex) else { return nil }
        return frames[currentFrameIndex]
    }

    func setImageData(_ data: Data, for slot: Slot) async {
        morphTask?.cancel()
        morphTask = nil
        resetResults()
        stage = .loading
        do {
            let result = try await Task.detached(priority: .userInitiated) {
                let loaded = try ImageLoader.load(data: data, maxPixelSize: 600)
                let cropped = try FaceCropper().crop(loaded)
                let landmarks = try FaceDetector().landmarks(in: cropped)
                return (cropped, landmarks)
            }.value

            guard let preview = uiImage(from: result.0) else {
                throw MorpherError.imageSizeMismatch
            }

            switch slot {
            case .first:
                firstImage = result.0
                firstLandmarks = result.1
                firstPreview = preview
            case .second:
                secondImage = result.0
                secondLandmarks = result.1
                secondPreview = preview
            }
            resetResults()
            stage = canMorph ? .ready : .empty
        } catch {
            switch slot {
            case .first:
                firstImage = nil
                firstLandmarks = nil
                firstPreview = nil
            case .second:
                secondImage = nil
                secondLandmarks = nil
                secondPreview = nil
            }
            stage = canMorph ? .ready : .empty
            errorMessage = friendlyMessage(error)
        }
    }

    func setPreparedImages(
        firstImage: ImageBuffer,
        firstLandmarks: Landmarks,
        firstPreview: UIImage,
        secondImage: ImageBuffer,
        secondLandmarks: Landmarks,
        secondPreview: UIImage
    ) {
        self.firstImage = firstImage
        self.firstLandmarks = firstLandmarks
        self.firstPreview = firstPreview
        self.secondImage = secondImage
        self.secondLandmarks = secondLandmarks
        self.secondPreview = secondPreview
        resetResults()
        stage = canMorph ? .ready : .empty
    }

    func morph() {
        guard let firstImage,
              let secondImage,
              let firstLandmarks,
              let secondLandmarks else {
            return
        }

        morphTask?.cancel()
        pause()
        resetResults()
        stage = .processing(completed: 0, total: 24)

        morphTask = Task { [weak self] in
            guard let self else { return }
            do {
                var buffers: [ImageBuffer] = []
                for try await frame in SequenceGenerator.frames(
                    firstImage,
                    secondImage,
                    landmarks1: firstLandmarks,
                    landmarks2: secondLandmarks,
                    options: SequenceOptions(frameCount: 24)
                ) {
                    try Task.checkCancellation()
                    buffers.append(frame.image)
                    if let image = self.uiImage(from: frame.image) {
                        self.frames.append(image)
                        self.currentFrameIndex = self.frames.count - 1
                    }
                    self.stage = .processing(
                        completed: frame.completed,
                        total: frame.total
                    )
                }

                self.frames = buffers.compactMap { self.uiImage(from: $0) }
                self.currentFrameIndex = 0
                self.stage = .finished
                self.play()

                let url = try await self.encodeVideo(frames: buffers)
                try Task.checkCancellation()
                self.videoURL = url
                self.savedToPhotos = false

                if let thumbnail = self.frames[safe: self.frames.count / 2] {
                    _ = try self.historyStore.save(
                        videoURL: url,
                        thumbnail: thumbnail
                    )
                    self.historyRecords = self.historyStore.records
                }
            } catch is CancellationError {
                self.stage = self.canMorph ? .ready : .empty
            } catch {
                self.stage = self.canMorph ? .ready : .empty
                self.errorMessage = self.friendlyMessage(error)
            }
        }
    }

    func cancelMorph() {
        morphTask?.cancel()
        morphTask = nil
        pause()
        stage = canMorph ? .ready : .empty
    }

    func play() {
        guard frames.count > 1 else { return }
        isPlaying = true
        playbackTask?.cancel()
        playbackTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 70_000_000)
                guard let self, !Task.isCancelled else { return }
                self.currentFrameIndex = (self.currentFrameIndex + 1)
                    % self.frames.count
            }
        }
    }

    func pause() {
        isPlaying = false
        playbackTask?.cancel()
        playbackTask = nil
    }

    func saveToPhotos() async {
        guard let videoURL else { return }
        let status: PHAuthorizationStatus = await withCheckedContinuation {
            continuation in
            PHPhotoLibrary.requestAuthorization(for: .addOnly) {
                continuation.resume(returning: $0)
            }
        }
        guard status == .authorized || status == .limited else {
            errorMessage = "Photo library access is required to save videos."
            return
        }

        do {
            try await withCheckedThrowingContinuation {
                (continuation: CheckedContinuation<Void, Error>) in
                PHPhotoLibrary.shared().performChanges {
                    PHAssetChangeRequest.creationRequestForAssetFromVideo(
                        atFileURL: videoURL
                    )
                } completionHandler: { success, error in
                    if success {
                        continuation.resume()
                    } else {
                        continuation.resume(
                            throwing: error ?? NSError(
                                domain: "ImageMorpher",
                                code: -1,
                                userInfo: [
                                    NSLocalizedDescriptionKey:
                                        "Could not save the video to Photos.",
                                ]
                            )
                        )
                    }
                }
            }
            savedToPhotos = true
        } catch {
            errorMessage = friendlyMessage(error)
        }
    }

    func deleteHistory(_ record: MorphRecord) {
        historyStore.delete(record)
        historyRecords = historyStore.records
    }

    func thumbnail(for record: MorphRecord) -> UIImage? {
        historyStore.thumbnail(for: record)
    }

    func videoURL(for record: MorphRecord) -> URL {
        historyStore.videoURL(for: record)
    }

    private func resetResults() {
        pause()
        frames = []
        currentFrameIndex = 0
        videoURL = nil
        savedToPhotos = false
    }

    private func encodeVideo(frames: [ImageBuffer]) async throws -> URL {
        let hevcURL = videoURL(for: "hevc")
        do {
            return try await encode(frames: frames, to: hevcURL, codec: .hevc)
        } catch {
            try? FileManager.default.removeItem(at: hevcURL)
            return try await encode(
                frames: frames,
                to: videoURL(for: "h264"),
                codec: .h264
            )
        }
    }

    private func encode(
        frames: [ImageBuffer],
        to url: URL,
        codec: VideoEncoderOptions.Codec
    ) async throws -> URL {
        guard let first = frames.first else {
            throw MorpherError.triangulationFailed
        }
        return try await Task.detached(priority: .userInitiated) {
            let encoder = try VideoEncoder(
                url: url,
                width: first.width,
                height: first.height,
                options: VideoEncoderOptions(codec: codec, frameRate: 12)
            )
            for frame in frames {
                try encoder.append(frame)
            }
            try await encoder.finish()
            return url
        }.value
    }

    private func videoURL(for codec: String) -> URL {
        FileManager.default.temporaryDirectory
            .appendingPathComponent("morph-\(codec)-\(UUID().uuidString)")
            .appendingPathExtension("mp4")
    }

    private func uiImage(from buffer: ImageBuffer) -> UIImage? {
        guard let cgImage = buffer.makeCGImage() else { return nil }
        return UIImage(cgImage: cgImage)
    }

    private func friendlyMessage(_ error: Error) -> String {
        if let error = error as? FaceCropperError {
            switch error {
            case .noFaceDetected:
                return "No face was detected in that photo."
            case .visionFailure(let message):
                return "Face detection failed: \(message)"
            case .invalidImage, .renderingFailed:
                return "That photo could not be processed."
            }
        }
        if let error = error as? LandmarkError {
            switch error {
            case .noFaceDetected:
                return "No face landmarks were found in that photo."
            case .visionFailure(let message):
                return "Face landmark detection failed: \(message)"
            case .missingRegion(let region):
                return "A required face region (\(region)) was missing."
            case .invalidRegion(let region, _):
                return "A face region (\(region)) was invalid."
            case .invalidImage:
                return "That photo could not be processed."
            }
        }
        if let error = error as? MorpherError {
            switch error {
            case .imageSizeMismatch:
                return "The two images must have the same dimensions."
            case .landmarkCountMismatch:
                return "The detected faces do not have matching landmarks."
            case .triangulationFailed:
                return "Could not build a triangulation for these faces."
            case .invalidTime, .invalidTriangle:
                return "The morph could not be generated."
            }
        }
        return error.localizedDescription
    }
}

private extension Array {
    subscript(safe index: Index) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}
