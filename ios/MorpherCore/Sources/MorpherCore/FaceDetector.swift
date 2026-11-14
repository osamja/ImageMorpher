import Foundation

/// Abstraction over face detection + landmark extraction.
///
/// The core morph pipeline only needs a set of corresponding feature points for
/// each image; it does not care where they come from. On Apple platforms a
/// `VisionFaceDetector` (wrapping `VNDetectFaceLandmarksRequest`) implements
/// this protocol. On Linux/tests a fixture or manual implementation supplies
/// the points, keeping the whole core buildable and testable off-device.
public protocol FaceDetector {
    /// Extracts ordered landmark points (face features, without corners) from
    /// an image. Throws if no face is found.
    func landmarks(in image: ImageBuffer) throws -> [Point]
}

/// Adds the four image corners to a landmark set so the triangulation covers
/// the whole image. Mirrors `addCornerPoints` in the Python reference.
public enum CornerPoints {
    public static func add(to points: [Point], width: Int, height: Int) -> [Point] {
        var pts = points
        pts.append(Point(0, 0))
        pts.append(Point(Double(width - 1), 0))
        pts.append(Point(0, Double(height - 1)))
        pts.append(Point(Double(width - 1), Double(height - 1)))
        return pts
    }
}
