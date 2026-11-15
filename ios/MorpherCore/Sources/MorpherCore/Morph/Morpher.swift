import Foundation

public enum MorpherError: Error, Equatable {
    case imageSizeMismatch
    case landmarkCountMismatch
    case invalidTriangle(index: Int)
    case invalidTime(Double)
    case triangulationFailed
}

public enum Morpher {
    public static func morph(
        _ image1: ImageBuffer,
        _ image2: ImageBuffer,
        t: Double
    ) throws -> ImageBuffer {
        guard image1.width == image2.width, image1.height == image2.height else {
            throw MorpherError.imageSizeMismatch
        }
        let detector = FaceDetector()
        let landmarks1 = try detector.landmarks(in: image1)
        let landmarks2 = try detector.landmarks(in: image2)
        return try morph(
            image1,
            image2,
            landmarks1: landmarks1,
            landmarks2: landmarks2,
            t: t
        )
    }

    public static func morph(
        _ image1: ImageBuffer,
        _ image2: ImageBuffer,
        landmarks1: Landmarks,
        landmarks2: Landmarks,
        t: Double
    ) throws -> ImageBuffer {
        guard image1.width == image2.width, image1.height == image2.height else {
            throw MorpherError.imageSizeMismatch
        }
        return try morph(
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
            t: t
        )
    }

    public static func morph(
        _ image1: ImageBuffer,
        _ image2: ImageBuffer,
        points1: [SIMD2<Double>],
        points2: [SIMD2<Double>],
        t: Double
    ) throws -> ImageBuffer {
        guard t >= 0, t <= 1 else {
            throw MorpherError.invalidTime(t)
        }
        guard image1.width == image2.width, image1.height == image2.height else {
            throw MorpherError.imageSizeMismatch
        }
        guard points1.count == points2.count, points1.count >= 3 else {
            throw MorpherError.landmarkCountMismatch
        }

        let midpoints = zip(points1, points2).map {
            $0 * (1 - t) + $1 * t
        }
        let triangles = Delaunay.triangulate(midpoints)
        guard !triangles.isEmpty else {
            throw MorpherError.triangulationFailed
        }

        let warper = AffineWarp()
        let warped1 = try warper.warp(
            image: image1,
            sourcePoints: points1,
            destinationPoints: midpoints,
            triangles: triangles
        )
        let warped2 = try warper.warp(
            image: image2,
            sourcePoints: points2,
            destinationPoints: midpoints,
            triangles: triangles
        )
        return try Dissolve.blend(warped1, warped2, t: t)
    }
}
