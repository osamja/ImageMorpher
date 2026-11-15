import XCTest

@testable import MorpherCore

final class MorpherTests: XCTestCase {
    private struct MorphFixture: Decodable {
        struct Case: Decodable {
            let t: Double
            let expected: [UInt8]
        }

        let width: Int
        let height: Int
        let image1: [UInt8]
        let image2: [UInt8]
        let points1: [[Double]]
        let points2: [[Double]]
        let cases: [Case]
    }

    func testParityWithPythonReference() throws {
        let url = try TestSupport.fixtureURL(named: "morph_python_32")
        let fixture = try JSONDecoder().decode(
            MorphFixture.self,
            from: Data(contentsOf: url)
        )
        let image1 = try ImageBuffer(
            width: fixture.width,
            height: fixture.height,
            pixels: fixture.image1
        )
        let image2 = try ImageBuffer(
            width: fixture.width,
            height: fixture.height,
            pixels: fixture.image2
        )
        let points1 = fixture.points1.map { SIMD2<Double>($0[0], $0[1]) }
        let points2 = fixture.points2.map { SIMD2<Double>($0[0], $0[1]) }
        let lastPixelOffset = (fixture.width * fixture.height - 1) * 4

        for testCase in fixture.cases {
            let result = try Morpher.morph(
                image1,
                image2,
                points1: points1,
                points2: points2,
                t: testCase.t
            )

            var totalDifference = 0
            var comparedChannels = 0
            var channelsWithinTolerance = 0
            for offset in stride(from: 0, to: result.pixels.count, by: 4) {
                if offset == lastPixelOffset { continue }
                for channel in 0..<3 {
                    let difference = abs(
                        Int(result.pixels[offset + channel])
                            - Int(testCase.expected[offset + channel])
                    )
                    totalDifference += difference
                    comparedChannels += 1
                    if difference <= 8 {
                        channelsWithinTolerance += 1
                    }
                }
            }

            let meanDifference = Double(totalDifference) / Double(comparedChannels)
            let withinTolerance = Double(channelsWithinTolerance) / Double(comparedChannels)
            XCTAssertLessThan(meanDifference, 2.0, "t=\(testCase.t)")
            XCTAssertGreaterThan(withinTolerance, 0.98, "t=\(testCase.t)")
        }
    }

    func testEndpointsReproduceInputs() throws {
        let image1 = TestSupport.gradientImage(width: 32, height: 32)
        var image2 = TestSupport.gradientImage(width: 32, height: 32)
        for y in 0..<32 {
            for x in 0..<32 {
                let color = image2[x, y]
                image2[x, y] = RGBA(
                    r: color.r &+ 37,
                    g: color.g &+ 23,
                    b: color.b &+ 11,
                    a: color.a
                )
            }
        }
        let points1 = TestSupport.gridPoints(
            width: 32,
            height: 32,
            columns: 4,
            rows: 4
        )
        let points2 = points1

        XCTAssertEqual(
            try Morpher.morph(
                image1,
                image2,
                points1: points1,
                points2: points2,
                t: 0
            ),
            image1
        )
        XCTAssertEqual(
            try Morpher.morph(
                image1,
                image2,
                points1: points1,
                points2: points2,
                t: 1
            ),
            image2
        )
    }

    func testSolidColorsBlendAtMidpoint() throws {
        let image1 = TestSupport.solidImage(
            width: 16,
            height: 16,
            color: RGBA(r: 255, g: 0, b: 100)
        )
        let image2 = TestSupport.solidImage(
            width: 16,
            height: 16,
            color: RGBA(r: 0, g: 255, b: 200)
        )
        let points = TestSupport.gridPoints(
            width: 16,
            height: 16,
            columns: 2,
            rows: 2
        )

        let morphed = try Morpher.morph(
            image1,
            image2,
            points1: points,
            points2: points,
            t: 0.5
        )

        for y in 0..<morphed.height {
            for x in 0..<morphed.width {
                XCTAssertEqual(
                    morphed[x, y],
                    RGBA(r: 127, g: 127, b: 150, a: 254)
                )
            }
        }
    }

    func testCroppedFacesMorphEndToEnd() throws {
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

        let morphed = try Morpher.morph(image1, image2, t: 0.5)

        XCTAssertEqual(morphed.width, 500)
        XCTAssertEqual(morphed.height, 500)
        XCTAssertGreaterThan(Set(morphed.pixels).count, 64)
    }

    func testInvalidTimeThrows() {
        let image = TestSupport.solidImage(width: 4, height: 4, color: .black)
        let points = TestSupport.gridPoints(
            width: 4,
            height: 4,
            columns: 1,
            rows: 1
        )

        XCTAssertThrowsError(
            try Morpher.morph(
                image,
                image,
                points1: points,
                points2: points,
                t: 1.5
            )
        ) { error in
            XCTAssertEqual(error as? MorpherError, .invalidTime(1.5))
        }
    }

    func testSizeMismatchThrows() {
        let points = TestSupport.gridPoints(
            width: 4,
            height: 4,
            columns: 1,
            rows: 1
        )

        XCTAssertThrowsError(
            try Morpher.morph(
                TestSupport.solidImage(width: 4, height: 4, color: .black),
                TestSupport.solidImage(width: 5, height: 4, color: .black),
                points1: points,
                points2: points,
                t: 0.5
            )
        ) { error in
            XCTAssertEqual(error as? MorpherError, .imageSizeMismatch)
        }
    }

    func testLandmarkCountMismatchThrows() {
        let image = TestSupport.solidImage(width: 4, height: 4, color: .black)

        XCTAssertThrowsError(
            try Morpher.morph(
                image,
                image,
                points1: [SIMD2(0, 0), SIMD2(4, 0), SIMD2(0, 4)],
                points2: [SIMD2(0, 0), SIMD2(4, 0)],
                t: 0.5
            )
        ) { error in
            XCTAssertEqual(error as? MorpherError, .landmarkCountMismatch)
        }
    }
}
