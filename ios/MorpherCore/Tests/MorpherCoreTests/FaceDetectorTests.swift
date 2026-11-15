import XCTest

@testable import MorpherCore

final class FaceDetectorTests: XCTestCase {
    func testDetectsStableLandmarks() throws {
        let image = try ImageLoader.load(
            contentsOf: TestSupport.inputImage("face-1.jpeg")
        )
        let landmarks = try FaceDetector().landmarks(in: image)

        XCTAssertEqual(landmarks.points.count, Landmarks.regionPointCount)
        for point in landmarks.points {
            XCTAssertTrue(point.x.isFinite)
            XCTAssertTrue(point.y.isFinite)
            XCTAssertGreaterThanOrEqual(point.x, -1)
            XCTAssertGreaterThanOrEqual(point.y, -1)
            XCTAssertLessThanOrEqual(point.x, Double(image.width) + 1)
            XCTAssertLessThanOrEqual(point.y, Double(image.height) + 1)
        }

        let withCorners = landmarks.pointsWithCorners(
            width: image.width,
            height: image.height
        )
        XCTAssertEqual(withCorners.count, 72)
        XCTAssertEqual(
            Array(withCorners.suffix(4)),
            [
                SIMD2(0, 0),
                SIMD2(0, 427),
                SIMD2(500, 0),
                SIMD2(500, 427),
            ]
        )
    }

    func testLandmarkDetectionIsDeterministic() throws {
        let image = try ImageLoader.load(
            contentsOf: TestSupport.inputImage("face-1.jpeg")
        )
        let detector = FaceDetector()

        XCTAssertEqual(
            try detector.landmarks(in: image),
            try detector.landmarks(in: image)
        )
    }

    func testLandmarksForDifferentFacesHaveSameCount() throws {
        let first = try FaceDetector().landmarks(
            in: ImageLoader.load(
                contentsOf: TestSupport.inputImage("face-1.jpeg")
            )
        )
        let second = try FaceDetector().landmarks(
            in: ImageLoader.load(
                contentsOf: TestSupport.inputImage("face-2.jpeg")
            )
        )

        XCTAssertEqual(
            first.pointsWithCorners(width: 500, height: 500).count,
            second.pointsWithCorners(width: 500, height: 500).count
        )
    }

    func testEyeLandmarksAreAboveMouthLandmarks() throws {
        let image = try ImageLoader.load(
            contentsOf: TestSupport.inputImage("face-1.jpeg")
        )
        let points = try FaceDetector().landmarks(in: image).points

        let eyes = points[36..<48]
        let lips = points[48..<68]
        let eyeAverage = eyes.map(\.y).reduce(0, +) / Double(eyes.count)
        let lipAverage = lips.map(\.y).reduce(0, +) / Double(lips.count)

        XCTAssertLessThan(eyeAverage, lipAverage)
    }

    func testThrowsWhenNoFaceDetected() {
        let blank = ImageBuffer(
            width: 64,
            height: 64,
            fill: RGBA(r: 128, g: 128, b: 128)
        )

        XCTAssertThrowsError(try FaceDetector().landmarks(in: blank)) { error in
            XCTAssertEqual(error as? LandmarkError, .noFaceDetected)
        }
    }
}

final class LandmarkResamplerTests: XCTestCase {
    func testOpenResamplingIncludesBothEndpoints() {
        let points = [
            SIMD2<Double>(0, 0),
            SIMD2<Double>(10, 0),
        ]

        let result = LandmarkResampler.resample(points, count: 3, closed: false)

        XCTAssertEqual(result.count, 3)
        XCTAssertEqual(result[0], SIMD2<Double>(0, 0))
        XCTAssertEqual(result[1], SIMD2<Double>(5, 0))
        XCTAssertEqual(result[2], SIMD2<Double>(10, 0))
    }

    func testClosedResamplingSpacesSamplesAroundLoop() {
        let points = [
            SIMD2<Double>(0, 0),
            SIMD2<Double>(10, 0),
            SIMD2<Double>(10, 10),
            SIMD2<Double>(0, 10),
        ]

        let result = LandmarkResampler.resample(points, count: 4, closed: true)

        XCTAssertEqual(result.count, 4)
        XCTAssertEqual(result[0], SIMD2<Double>(0, 0))
        XCTAssertEqual(result[1], SIMD2<Double>(10, 0))
        XCTAssertEqual(result[2], SIMD2<Double>(10, 10))
        XCTAssertEqual(result[3], SIMD2<Double>(0, 10))
    }

    func testEmptyAndSinglePointInputs() {
        XCTAssertTrue(
            LandmarkResampler.resample([], count: 3, closed: false).isEmpty
        )

        let single = [SIMD2<Double>(3, 4)]
        XCTAssertEqual(
            LandmarkResampler.resample(single, count: 2, closed: false),
            [SIMD2<Double>(3, 4), SIMD2<Double>(3, 4)]
        )
    }
}
