import XCTest
@testable import MorpherCore

final class MorphTests: XCTestCase {

    private let red = ImageBuffer(width: 16, height: 16, color: (r: 255, g: 0, b: 0))
    private let blue = ImageBuffer(width: 16, height: 16, color: (r: 0, g: 0, b: 255))

    private func cornerPoints() -> [Point] {
        CornerPoints.add(to: [Point(8, 8)], width: 16, height: 16)
    }

    func testMorphT0ReproducesFirstImage() {
        let out = Morpher.morph(red, blue, points1: cornerPoints(), points2: cornerPoints(), t: 0)
        XCTAssertEqual(out.pixel(x: 8, y: 8).r, 255)
        XCTAssertEqual(out.pixel(x: 8, y: 8).b, 0)
    }

    func testMorphT1ReproducesSecondImage() {
        let out = Morpher.morph(red, blue, points1: cornerPoints(), points2: cornerPoints(), t: 1)
        XCTAssertEqual(out.pixel(x: 8, y: 8).r, 0)
        XCTAssertEqual(out.pixel(x: 8, y: 8).b, 255)
    }

    func testMorphHalfwayIsAverage() {
        let out = Morpher.morph(red, blue, points1: cornerPoints(), points2: cornerPoints(), t: 0.5)
        let p = out.pixel(x: 8, y: 8)
        XCTAssertEqual(p.r, 128)
        XCTAssertEqual(p.g, 0)
        XCTAssertEqual(p.b, 128)
    }

    func testMorphSequenceProducesOrderedFrames() async {
        let frames = await SequenceGenerator.frames(
            from: red, to: blue,
            points1: cornerPoints(), points2: cornerPoints(),
            stepSize: 50
        )
        XCTAssertEqual(frames.count, 3)
        XCTAssertEqual(frames[0].pixel(x: 8, y: 8).r, 255)
        XCTAssertEqual(frames[1].pixel(x: 8, y: 8).r, 128)
        XCTAssertEqual(frames[2].pixel(x: 8, y: 8).b, 255)
    }
}
