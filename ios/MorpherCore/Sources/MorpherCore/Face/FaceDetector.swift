import CoreGraphics
import Foundation
import Vision

public struct FaceDetector {
    public init() {}

    public func landmarks(in image: ImageBuffer) throws -> Landmarks {
        guard let cgImage = image.makeCGImage() else {
            throw LandmarkError.invalidImage
        }

        let request = VNDetectFaceLandmarksRequest()
        let handler = VNImageRequestHandler(cgImage: cgImage, orientation: .up)
        do {
            try handler.perform([request])
        } catch {
            throw LandmarkError.visionFailure(error.localizedDescription)
        }

        let observations = request.results ?? []
        let face = observations.max {
            $0.boundingBox.width * $0.boundingBox.height
                < $1.boundingBox.width * $1.boundingBox.height
        }
        guard let face, let visionLandmarks = face.landmarks else {
            throw LandmarkError.noFaceDetected
        }

        var points: [SIMD2<Double>] = []
        points.reserveCapacity(Landmarks.regionPointCount)

        for regionName in LandmarkRegion.allCases {
            guard let visionRegion = region(from: visionLandmarks, name: regionName) else {
                throw LandmarkError.missingRegion(regionName.rawValue)
            }
            let imagePoints = mapToImage(
                visionRegion,
                face: face,
                width: image.width,
                height: image.height
            )
            guard !imagePoints.isEmpty else {
                throw LandmarkError.invalidRegion(regionName.rawValue, pointCount: 0)
            }
            points.append(
                contentsOf: LandmarkResampler.resample(
                    imagePoints,
                    count: regionName.targetCount,
                    closed: regionName.isClosed
                )
            )
        }

        guard points.count == Landmarks.regionPointCount else {
            throw LandmarkError.invalidRegion(
                "combined",
                pointCount: points.count
            )
        }
        return Landmarks(points: points)
    }

    private func region(
        from landmarks: VNFaceLandmarks2D,
        name: LandmarkRegion
    ) -> VNFaceLandmarkRegion2D? {
        switch name {
        case .faceContour: return landmarks.faceContour
        case .rightEyebrow: return landmarks.rightEyebrow
        case .leftEyebrow: return landmarks.leftEyebrow
        case .noseCrest: return landmarks.noseCrest
        case .nose: return landmarks.nose
        case .rightEye: return landmarks.rightEye
        case .leftEye: return landmarks.leftEye
        case .outerLips: return landmarks.outerLips
        case .innerLips: return landmarks.innerLips
        }
    }

    private func mapToImage(
        _ region: VNFaceLandmarkRegion2D,
        face: VNFaceObservation,
        width: Int,
        height: Int
    ) -> [SIMD2<Double>] {
        let bounds = face.boundingBox
        return region.normalizedPoints.map { point in
            let normalizedX = bounds.origin.x + Double(point.x) * bounds.width
            let normalizedY = bounds.origin.y + Double(point.y) * bounds.height
            return SIMD2(
                normalizedX * Double(width),
                (1 - normalizedY) * Double(height)
            )
        }
    }
}
