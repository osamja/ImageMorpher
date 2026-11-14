import Foundation

/// Minimal PPM (P6, binary RGB) reader/writer.
///
/// PPM is used because it is dependency-free to read/write in pure Swift and is
/// trivially produced by the Python reference implementation (`imageio`, PIL,
/// scikit-image) for parity fixtures on Linux, where Apple's image frameworks
/// are unavailable.
public enum PPMImage {
    public enum PPMError: Error, CustomStringConvertible {
        case invalidHeader(String)

        public var description: String {
            switch self {
            case .invalidHeader(let msg): return "Invalid PPM: \(msg)"
            }
        }
    }

    public static func write(_ image: ImageBuffer, to url: URL) throws {
        let header = "P6\n\(image.width) \(image.height)\n255\n"
        var data = Data(header.utf8)
        for y in 0..<image.height {
            for x in 0..<image.width {
                let p = image.pixel(x: x, y: y)
                data.append(p.r)
                data.append(p.g)
                data.append(p.b)
            }
        }
        try data.write(to: url)
    }

    public static func read(_ data: Data) throws -> ImageBuffer {
        let bytes = [UInt8](data)
        var pos = 0

        func isSpace(_ b: UInt8) -> Bool {
            b == 32 || b == 9 || b == 10 || b == 13
        }

        func readToken() throws -> String {
            // Skip whitespace and comments.
            while pos < bytes.count {
                let b = bytes[pos]
                if b == 35 { // '#'
                    while pos < bytes.count && bytes[pos] != 10 { pos += 1 }
                } else if isSpace(b) {
                    pos += 1
                } else {
                    break
                }
            }
            let start = pos
            while pos < bytes.count && !isSpace(bytes[pos]) { pos += 1 }
            guard pos > start, let token = String(bytes: bytes[start..<pos], encoding: .utf8) else {
                throw PPMError.invalidHeader("unexpected end of token")
            }
            return token
        }

        let magic = try readToken()
        guard magic == "P6" else { throw PPMError.invalidHeader("expected P6, got \(magic)") }
        guard let width = Int(try readToken()) else { throw PPMError.invalidHeader("bad width") }
        guard let height = Int(try readToken()) else { throw PPMError.invalidHeader("bad height") }
        guard let maxval = Int(try readToken()) else { throw PPMError.invalidHeader("bad maxval") }
        guard maxval == 255 else { throw PPMError.invalidHeader("only maxval 255 supported, got \(maxval)") }

        // Exactly one whitespace byte separates the header from the raster.
        guard pos < bytes.count else { throw PPMError.invalidHeader("missing raster") }
        pos += 1

        let expected = width * height * 3
        guard bytes.count - pos >= expected else { throw PPMError.invalidHeader("raster too short") }

        var image = ImageBuffer(width: width, height: height)
        var i = 0
        for y in 0..<height {
            for x in 0..<width {
                let r = bytes[pos + i]
                let g = bytes[pos + i + 1]
                let b = bytes[pos + i + 2]
                image.setPixel(x: x, y: y, r: r, g: g, b: b)
                i += 3
            }
        }
        return image
    }
}
