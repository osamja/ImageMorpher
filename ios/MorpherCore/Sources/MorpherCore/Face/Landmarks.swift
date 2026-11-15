import Foundation

public struct Landmarks: Equatable, Sendable {
    public static let regionPointCount = 68
    public static let cornerCount = 4

    public let points: [SIMD2<Double>]

    public init(points: [SIMD2<Double>]) {
        precondition(
            points.count == Landmarks.regionPointCount,
            "Landmarks require \(Landmarks.regionPointCount) points"
        )
        self.points = points
    }

    public func pointsWithCorners(width: Int, height: Int) -> [SIMD2<Double>] {
        let width = Double(width)
        let height = Double(height)
        return points + [
            SIMD2(0, 0),
            SIMD2(0, height),
            SIMD2(width, 0),
            SIMD2(width, height),
        ]
    }
}

public enum LandmarkError: Error, Equatable {
    case noFaceDetected
    case invalidImage
    case missingRegion(String)
    case invalidRegion(String, pointCount: Int)
    case visionFailure(String)
}

enum LandmarkRegion: String, CaseIterable {
    case faceContour
    case rightEyebrow
    case leftEyebrow
    case noseCrest
    case nose
    case rightEye
    case leftEye
    case outerLips
    case innerLips

    var targetCount: Int {
        switch self {
        case .faceContour: return 17
        case .rightEyebrow, .leftEyebrow: return 5
        case .noseCrest: return 4
        case .nose: return 5
        case .rightEye, .leftEye: return 6
        case .outerLips: return 12
        case .innerLips: return 8
        }
    }

    var isClosed: Bool {
        switch self {
        case .rightEye, .leftEye, .outerLips, .innerLips:
            return true
        case .faceContour, .rightEyebrow, .leftEyebrow, .noseCrest, .nose:
            return false
        }
    }
}

enum LandmarkResampler {
    static func resample(
        _ points: [SIMD2<Double>],
        count: Int,
        closed: Bool
    ) -> [SIMD2<Double>] {
        guard count > 0 else { return [] }
        guard let first = points.first else { return [] }
        guard points.count > 1 else {
            return Array(repeating: first, count: count)
        }

        var source = points
        if closed {
            source.append(first)
        }

        var segmentLengths: [Double] = []
        segmentLengths.reserveCapacity(source.count - 1)
        var totalLength = 0.0
        for index in 1..<source.count {
            let delta = source[index] - source[index - 1]
            let length = (delta.x * delta.x + delta.y * delta.y).squareRoot()
            segmentLengths.append(length)
            totalLength += length
        }

        guard totalLength > 0 else {
            return Array(repeating: first, count: count)
        }

        let denominator = closed ? count : max(count - 1, 1)
        var result: [SIMD2<Double>] = []
        result.reserveCapacity(count)

        for sample in 0..<count {
            let target = totalLength * Double(sample) / Double(denominator)
            var traversed = 0.0
            var segment = 0
            while segment < segmentLengths.count - 1,
                  traversed + segmentLengths[segment] < target {
                traversed += segmentLengths[segment]
                segment += 1
            }
            let length = segmentLengths[segment]
            let fraction = length > 0 ? (target - traversed) / length : 0
            let start = source[segment]
            let end = source[segment + 1]
            result.append(start + (end - start) * fraction)
        }

        return result
    }
}
