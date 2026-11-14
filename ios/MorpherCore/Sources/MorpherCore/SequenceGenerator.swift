import Foundation

/// Generates a morph sequence (a list of frames) between two images.
///
/// Frames are produced concurrently in bounded chunks; each frame is an
/// independent `Morpher.morph` call.
public enum SequenceGenerator {

    /// Generates the frames of a morph sequence.
    ///
    /// - Parameters:
    ///   - stepSize: Distance between consecutive `t` values on a 0...100 scale.
    ///     Mirrors the Python reference's `range(0, 101, stepSize)` semantics
    ///     (e.g. `20` yields frames at t = 0.0, 0.2, ..., 1.0).
    ///   - maxConcurrent: Bound on in-flight frame renders per chunk.
    /// - Returns: Frames in ascending `t` order.
    public static func frames(
        from img1: ImageBuffer,
        to img2: ImageBuffer,
        points1: [Point],
        points2: [Point],
        stepSize: Int = 20,
        maxConcurrent: Int = ProcessInfo.processInfo.activeProcessorCount
    ) async -> [ImageBuffer] {
        precondition(stepSize >= 1, "stepSize must be >= 1")

        let tValues = stride(from: 0, through: 100, by: stepSize).map { Double($0) / 100.0 }
        let limit = max(1, maxConcurrent)
        var results: [ImageBuffer?] = Array(repeating: nil, count: tValues.count)

        var cursor = 0
        while cursor < tValues.count {
            let end = min(cursor + limit, tValues.count)
            await withTaskGroup(of: (Int, ImageBuffer).self) { group in
                for index in cursor..<end {
                    let t = tValues[index]
                    group.addTask {
                        (index, Morpher.morph(img1, img2, points1: points1, points2: points2, t: t))
                    }
                }
                for await (index, image) in group {
                    results[index] = image
                }
            }
            cursor = end
        }

        return results.compactMap { $0 }
    }
}
