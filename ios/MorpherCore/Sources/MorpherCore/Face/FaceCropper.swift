import CoreGraphics
import Foundation
import Vision

public enum FaceCropperError: Error, Equatable {
    case noFaceDetected
    case invalidImage
    case renderingFailed
    case visionFailure(String)
}

public struct FaceCropper {
    public var outputSize: Int
    public var paddingFactor: Double

    public init(outputSize: Int = 500, paddingFactor: Double = 1.8) {
        precondition(outputSize > 0, "outputSize must be positive")
        precondition(paddingFactor > 0, "paddingFactor must be positive")
        self.outputSize = outputSize
        self.paddingFactor = paddingFactor
    }

    public func crop(_ image: ImageBuffer) throws -> ImageBuffer {
        guard let cgImage = image.makeCGImage() else {
            throw FaceCropperError.invalidImage
        }

        let request = VNDetectFaceRectanglesRequest()
        let handler = VNImageRequestHandler(cgImage: cgImage, orientation: .up)
        do {
            try handler.perform([request])
        } catch {
            throw FaceCropperError.visionFailure(error.localizedDescription)
        }

        let observations = request.results ?? []
        let face = observations.max {
            $0.boundingBox.width * $0.boundingBox.height
                < $1.boundingBox.width * $1.boundingBox.height
        }
        guard let face else {
            throw FaceCropperError.noFaceDetected
        }

        let bounds = face.boundingBox
        let width = CGFloat(cgImage.width)
        let height = CGFloat(cgImage.height)
        let faceRect = CGRect(
            x: bounds.minX * width,
            y: bounds.minY * height,
            width: bounds.width * width,
            height: bounds.height * height
        )
        let side = max(faceRect.width, faceRect.height) * CGFloat(paddingFactor)
        guard side > 0 else {
            throw FaceCropperError.invalidImage
        }

        let center = CGPoint(x: faceRect.midX, y: faceRect.midY)
        let output = CGFloat(outputSize)
        let scale = output / side
        let roll = CGFloat(face.roll?.doubleValue ?? 0)

        guard let context = CGContext(
            data: nil,
            width: outputSize,
            height: outputSize,
            bitsPerComponent: 8,
            bytesPerRow: outputSize * 4,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            throw FaceCropperError.renderingFailed
        }

        context.setFillColor(CGColor(red: 0, green: 0, blue: 0, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: output, height: output))
        context.interpolationQuality = .high
        context.translateBy(x: output / 2, y: output / 2)
        context.scaleBy(x: scale, y: scale)
        context.rotate(by: -roll)
        context.translateBy(x: -center.x, y: -center.y)
        context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))

        guard let cropped = context.makeImage() else {
            throw FaceCropperError.renderingFailed
        }
        return try ImageBuffer(cgImage: cropped)
    }
}
