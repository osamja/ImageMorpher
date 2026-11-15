import Foundation

public struct AffineWarp {
    public init() {}

    public func warp(
        image: ImageBuffer,
        sourcePoints: [SIMD2<Double>],
        destinationPoints: [SIMD2<Double>],
        triangles: [Triangle]
    ) throws -> ImageBuffer {
        guard sourcePoints.count == destinationPoints.count else {
            throw MorpherError.landmarkCountMismatch
        }

        var output = ImageBuffer(
            width: image.width,
            height: image.height,
            fill: .black
        )

        for (triangleIndex, triangle) in triangles.enumerated() {
            guard triangle.a < sourcePoints.count,
                  triangle.b < sourcePoints.count,
                  triangle.c < sourcePoints.count,
                  triangle.a < destinationPoints.count,
                  triangle.b < destinationPoints.count,
                  triangle.c < destinationPoints.count else {
                throw MorpherError.invalidTriangle(index: triangleIndex)
            }

            let source = TriangleVertices(
                a: sourcePoints[triangle.a],
                b: sourcePoints[triangle.b],
                c: sourcePoints[triangle.c]
            )
            let destination = TriangleVertices(
                a: destinationPoints[triangle.a],
                b: destinationPoints[triangle.b],
                c: destinationPoints[triangle.c]
            )

            let minX = max(
                0,
                Int(floor(min(destination.a.x, destination.b.x, destination.c.x)))
            )
            let maxX = min(
                image.width - 1,
                Int(ceil(max(destination.a.x, destination.b.x, destination.c.x)))
            )
            let minY = max(
                0,
                Int(floor(min(destination.a.y, destination.b.y, destination.c.y)))
            )
            let maxY = min(
                image.height - 1,
                Int(ceil(max(destination.a.y, destination.b.y, destination.c.y)))
            )
            guard minX <= maxX, minY <= maxY else { continue }

            for y in minY...maxY {
                for x in minX...maxX {
                    let point = SIMD2(Double(x), Double(y))
                    guard let weights = Barycentric.coordinates(
                        of: point,
                        in: destination
                    ) else {
                        continue
                    }
                    guard weights.x >= -1e-9,
                          weights.y >= -1e-9,
                          weights.z >= -1e-9 else {
                        continue
                    }

                    let sampled = Barycentric.interpolate(weights, in: source)
                    let sampleX = Int((sampled.x + 1e-9).rounded(.towardZero))
                    let sampleY = Int((sampled.y + 1e-9).rounded(.towardZero))
                    guard sampleX >= 0, sampleX < image.width,
                          sampleY >= 0, sampleY < image.height else {
                        continue
                    }
                    output[x, y] = image[sampleX, sampleY]
                }
            }
        }

        return output
    }
}
