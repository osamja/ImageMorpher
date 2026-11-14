import Foundation
import MorpherCore

// End-to-end demo: morph two synthetic "faces" (a checkerboard texture with a
// colored disc at a different position in each) and write the frames as PPM.
// Run with:  swift run morpher-demo [outputDirectory]
//
// This exercises the full pipeline (Delaunay -> inverse warp -> cross-dissolve)
// on Linux, producing inspectable images without any Apple frameworks.

let size = 256
let outDir = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "/tmp/morph-demo"

func makeImage(center: Point, color: (r: UInt8, g: UInt8, b: UInt8)) -> ImageBuffer {
    var img = ImageBuffer(width: size, height: size)
    // Checkerboard texture so warping is visible.
    for y in 0..<size {
        for x in 0..<size {
            let check = ((x / 16) + (y / 16)) % 2 == 0
            img.setPixel(x: x, y: y, r: check ? 200 : 60, g: check ? 200 : 60, b: check ? 200 : 60)
        }
    }
    // Colored disc.
    let radius = 45.0
    for y in 0..<size {
        for x in 0..<size {
            let dx = Double(x) - center.x
            let dy = Double(y) - center.y
            if dx * dx + dy * dy <= radius * radius {
                img.setPixel(x: x, y: y, r: color.r, g: color.g, b: color.b)
            }
        }
    }
    return img
}

func correspondingPoints(center: Point, radius: Double) -> [Point] {
    var pts = [center]
    let offsets: [(Double, Double)] = [
        (radius, 0), (-radius, 0), (0, radius), (0, -radius),
        (radius * 0.7071, radius * 0.7071), (radius * 0.7071, -radius * 0.7071),
        (-radius * 0.7071, radius * 0.7071), (-radius * 0.7071, -radius * 0.7071),
    ]
    for (dx, dy) in offsets {
        pts.append(Point(center.x + dx, center.y + dy))
    }
    return pts
}

let centerA = Point(80, 128)
let centerB = Point(176, 128)

let imgA = makeImage(center: centerA, color: (r: 255, g: 0, b: 0))
let imgB = makeImage(center: centerB, color: (r: 0, g: 0, b: 255))

let ptsA = CornerPoints.add(to: correspondingPoints(center: centerA, radius: 45),
                            width: size, height: size)
let ptsB = CornerPoints.add(to: correspondingPoints(center: centerB, radius: 45),
                            width: size, height: size)

try? FileManager.default.createDirectory(atPath: outDir, withIntermediateDirectories: true)

for t in [0.0, 0.25, 0.5, 0.75, 1.0] {
    let out = Morpher.morph(imgA, imgB, points1: ptsA, points2: ptsB, t: t)
    let url = URL(fileURLWithPath: "\(outDir)/morph_\(Int(t * 100)).ppm")
    do {
        try PPMImage.write(out, to: url)
        print("wrote \(url.path)")
    } catch {
        print("failed to write \(url.path): \(error)")
    }
}
