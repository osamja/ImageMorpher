import XCTest

@testable import MorpherCore

final class SequenceGeneratorTests: XCTestCase {
    func testFramesAreGeneratedInOrder() async throws {
        let image1 = TestSupport.solidImage(
            width: 16,
            height: 16,
            color: RGBA(r: 200, g: 10, b: 10)
        )
        let image2 = TestSupport.solidImage(
            width: 16,
            height: 16,
            color: RGBA(r: 10, g: 10, b: 200)
        )
        let points = TestSupport.gridPoints(
            width: 16,
            height: 16,
            columns: 2,
            rows: 2
        )

        var frames: [MorphFrame] = []
        for try await frame in SequenceGenerator.frames(
            image1,
            image2,
            points1: points,
            points2: points,
            options: SequenceOptions(
                frameCount: 5,
                maxConcurrentFrames: 2
            )
        ) {
            frames.append(frame)
        }

        XCTAssertEqual(frames.count, 5)
        XCTAssertEqual(frames.map(\.index), [0, 1, 2, 3, 4])
        XCTAssertEqual(frames.map(\.completed), [1, 2, 3, 4, 5])
        XCTAssertTrue(frames.allSatisfy { $0.total == 5 })
        XCTAssertEqual(frames.first?.image, image1)
        XCTAssertEqual(frames.last?.image, image2)
        XCTAssertEqual(
            frames[2].image[0, 0],
            RGBA(r: 105, g: 10, b: 105, a: 254)
        )
    }

    func testAutomaticLandmarkDetectionSequence() async throws {
        let cropper = FaceCropper()
        let image1 = try cropper.crop(
            ImageLoader.load(
                contentsOf: TestSupport.inputImage("face-1.jpeg")
            )
        )
        let image2 = try cropper.crop(
            ImageLoader.load(
                contentsOf: TestSupport.inputImage("face-2.jpeg")
            )
        )

        var frames: [MorphFrame] = []
        for try await frame in SequenceGenerator.frames(
            image1,
            image2,
            options: SequenceOptions(
                frameCount: 2,
                maxConcurrentFrames: 2
            )
        ) {
            frames.append(frame)
        }

        XCTAssertEqual(frames.count, 2)
        XCTAssertEqual(frames.map(\.index), [0, 1])
        XCTAssertEqual(frames[0].image, image1)
        XCTAssertEqual(frames[1].image, image2)
    }

    func testInvalidFrameCountThrows() async {
        let image = TestSupport.solidImage(width: 8, height: 8, color: .black)
        let points = TestSupport.gridPoints(
            width: 8,
            height: 8,
            columns: 1,
            rows: 1
        )

        do {
            for try await _ in SequenceGenerator.frames(
                image,
                image,
                points1: points,
                points2: points,
                options: SequenceOptions(frameCount: 0)
            ) {}
            XCTFail("Expected invalid frame count error")
        } catch {
            XCTAssertEqual(error as? SequenceError, .invalidFrameCount(0))
        }
    }
}
