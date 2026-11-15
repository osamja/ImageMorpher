import Foundation

public struct MorphFrame: Sendable {
    public let index: Int
    public let completed: Int
    public let total: Int
    public let image: ImageBuffer

    public init(index: Int, completed: Int, total: Int, image: ImageBuffer) {
        self.index = index
        self.completed = completed
        self.total = total
        self.image = image
    }
}

public struct SequenceOptions: Sendable {
    public var frameCount: Int
    public var maxConcurrentFrames: Int

    public init(frameCount: Int = 24, maxConcurrentFrames: Int? = nil) {
        self.frameCount = frameCount
        self.maxConcurrentFrames = maxConcurrentFrames
            ?? max(1, ProcessInfo.processInfo.activeProcessorCount)
    }
}

public enum SequenceError: Error, Equatable {
    case invalidFrameCount(Int)
    case invalidConcurrency(Int)
}

public enum SequenceGenerator {
    public static func frames(
        _ image1: ImageBuffer,
        _ image2: ImageBuffer,
        landmarks1: Landmarks,
        landmarks2: Landmarks,
        options: SequenceOptions = SequenceOptions()
    ) -> AsyncThrowingStream<MorphFrame, Error> {
        frames(
            image1,
            image2,
            points1: landmarks1.pointsWithCorners(
                width: image1.width,
                height: image1.height
            ),
            points2: landmarks2.pointsWithCorners(
                width: image2.width,
                height: image2.height
            ),
            options: options
        )
    }

    public static func frames(
        _ image1: ImageBuffer,
        _ image2: ImageBuffer,
        options: SequenceOptions = SequenceOptions()
    ) -> AsyncThrowingStream<MorphFrame, Error> {
        stream { continuation in
            guard image1.width == image2.width, image1.height == image2.height else {
                throw MorpherError.imageSizeMismatch
            }
            let detector = FaceDetector()
            let landmarks1 = try detector.landmarks(in: image1)
            let landmarks2 = try detector.landmarks(in: image2)
            try await generate(
                image1,
                image2,
                points1: landmarks1.pointsWithCorners(
                    width: image1.width,
                    height: image1.height
                ),
                points2: landmarks2.pointsWithCorners(
                    width: image2.width,
                    height: image2.height
                ),
                options: options,
                continuation: continuation
            )
        }
    }

    public static func frames(
        _ image1: ImageBuffer,
        _ image2: ImageBuffer,
        points1: [SIMD2<Double>],
        points2: [SIMD2<Double>],
        options: SequenceOptions = SequenceOptions()
    ) -> AsyncThrowingStream<MorphFrame, Error> {
        stream { continuation in
            try await generate(
                image1,
                image2,
                points1: points1,
                points2: points2,
                options: options,
                continuation: continuation
            )
        }
    }

    public static func generateFrames(
        _ image1: ImageBuffer,
        _ image2: ImageBuffer,
        points1: [SIMD2<Double>],
        points2: [SIMD2<Double>],
        options: SequenceOptions = SequenceOptions()
    ) async throws -> [ImageBuffer] {
        var images: [ImageBuffer] = []
        images.reserveCapacity(options.frameCount)
        for try await frame in frames(
            image1,
            image2,
            points1: points1,
            points2: points2,
            options: options
        ) {
            images.append(frame.image)
        }
        return images
    }

    private static func stream(
        _ body: @escaping (AsyncThrowingStream<MorphFrame, Error>.Continuation) async throws -> Void
    ) -> AsyncThrowingStream<MorphFrame, Error> {
        AsyncThrowingStream { continuation in
            let task = Task {
                do {
                    try await body(continuation)
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
            continuation.onTermination = { _ in
                task.cancel()
            }
        }
    }

    private static func generate(
        _ image1: ImageBuffer,
        _ image2: ImageBuffer,
        points1: [SIMD2<Double>],
        points2: [SIMD2<Double>],
        options: SequenceOptions,
        continuation: AsyncThrowingStream<MorphFrame, Error>.Continuation
    ) async throws {
        guard options.frameCount > 0 else {
            throw SequenceError.invalidFrameCount(options.frameCount)
        }
        guard options.maxConcurrentFrames > 0 else {
            throw SequenceError.invalidConcurrency(options.maxConcurrentFrames)
        }
        guard image1.width == image2.width, image1.height == image2.height else {
            throw MorpherError.imageSizeMismatch
        }
        guard points1.count == points2.count, points1.count >= 3 else {
            throw MorpherError.landmarkCountMismatch
        }

        let frameCount = options.frameCount
        let batchSize = min(options.maxConcurrentFrames, frameCount)

        for batchStart in stride(from: 0, to: frameCount, by: batchSize) {
            try Task.checkCancellation()
            let batchEnd = min(batchStart + batchSize, frameCount)
            let indices = Array(batchStart..<batchEnd)
            var results: [Int: ImageBuffer] = [:]
            results.reserveCapacity(indices.count)

            try await withThrowingTaskGroup(
                of: (Int, ImageBuffer).self
            ) { group in
                for index in indices {
                    group.addTask {
                        try Task.checkCancellation()
                        let t = frameCount == 1
                            ? 0
                            : Double(index) / Double(frameCount - 1)
                        let image = try Morpher.morph(
                            image1,
                            image2,
                            points1: points1,
                            points2: points2,
                            t: t
                        )
                        return (index, image)
                    }
                }
                for try await (index, image) in group {
                    results[index] = image
                }
            }

            for index in indices {
                try Task.checkCancellation()
                guard let image = results[index] else {
                    throw MorpherError.triangulationFailed
                }
                continuation.yield(
                    MorphFrame(
                        index: index,
                        completed: index + 1,
                        total: frameCount,
                        image: image
                    )
                )
            }
        }
    }
}
