import AVFoundation
import CoreVideo
import Foundation

public enum VideoEncoderError: Error, Equatable {
    case invalidDimensions(width: Int, height: Int)
    case invalidFrameRate(Int)
    case cannotCreateWriter
    case cannotAddInput
    case cannotStartWriting(String)
    case cannotCreatePixelBuffer
    case appendFailed(String)
    case finishFailed(String)
    case writerNotReady
    case imageSizeMismatch
}

public struct VideoEncoderOptions: Sendable {
    public enum Codec: Sendable {
        case h264
        case hevc
    }

    public var codec: Codec
    public var frameRate: Int
    public var bitRate: Int?

    public init(
        codec: Codec = .h264,
        frameRate: Int = 30,
        bitRate: Int? = nil
    ) {
        self.codec = codec
        self.frameRate = frameRate
        self.bitRate = bitRate
    }
}

public final class VideoEncoder {
    private let writer: AVAssetWriter
    private let input: AVAssetWriterInput
    private let adaptor: AVAssetWriterInputPixelBufferAdaptor
    private let width: Int
    private let height: Int
    private let frameRate: Int
    private var frameIndex: Int64 = 0
    private var didFinish = false

    public init(
        url: URL,
        width: Int,
        height: Int,
        options: VideoEncoderOptions = VideoEncoderOptions()
    ) throws {
        guard width > 0, height > 0, width % 2 == 0, height % 2 == 0 else {
            throw VideoEncoderError.invalidDimensions(width: width, height: height)
        }
        guard options.frameRate > 0 else {
            throw VideoEncoderError.invalidFrameRate(options.frameRate)
        }

        self.width = width
        self.height = height
        self.frameRate = options.frameRate

        try? FileManager.default.removeItem(at: url)
        do {
            writer = try AVAssetWriter(outputURL: url, fileType: .mp4)
        } catch {
            throw VideoEncoderError.cannotCreateWriter
        }

        var compression: [String: Any] = [
            AVVideoAverageBitRateKey: options.bitRate
                ?? max(width * height * 5, 1_000_000),
            AVVideoExpectedSourceFrameRateKey: options.frameRate,
        ]
        let codec: AVVideoCodecType
        switch options.codec {
        case .h264:
            codec = .h264
            compression[AVVideoProfileLevelKey] = AVVideoProfileLevelH264HighAutoLevel
        case .hevc:
            codec = .hevc
        }

        let settings: [String: Any] = [
            AVVideoCodecKey: codec,
            AVVideoWidthKey: width,
            AVVideoHeightKey: height,
            AVVideoCompressionPropertiesKey: compression,
        ]

        input = AVAssetWriterInput(mediaType: .video, outputSettings: settings)
        input.expectsMediaDataInRealTime = false

        let attributes: [String: Any] = [
            kCVPixelBufferPixelFormatTypeKey as String: Int(kCVPixelFormatType_32BGRA),
            kCVPixelBufferWidthKey as String: width,
            kCVPixelBufferHeightKey as String: height,
            kCVPixelBufferIOSurfacePropertiesKey as String: [:],
        ]
        adaptor = AVAssetWriterInputPixelBufferAdaptor(
            assetWriterInput: input,
            sourcePixelBufferAttributes: attributes
        )

        guard writer.canAdd(input) else {
            throw VideoEncoderError.cannotAddInput
        }
        writer.add(input)

        guard writer.startWriting() else {
            throw VideoEncoderError.cannotStartWriting(
                writer.error?.localizedDescription ?? "unknown error"
            )
        }
        writer.startSession(atSourceTime: .zero)
    }

    deinit {
        if writer.status == .writing {
            writer.cancelWriting()
        }
    }

    public func append(_ image: ImageBuffer) throws {
        guard image.width == width, image.height == height else {
            throw VideoEncoderError.imageSizeMismatch
        }
        guard !didFinish else {
            throw VideoEncoderError.writerNotReady
        }

        while !input.isReadyForMoreMediaData {
            if writer.status == .failed || writer.status == .cancelled {
                throw VideoEncoderError.appendFailed(
                    writer.error?.localizedDescription ?? "writer stopped"
                )
            }
            Thread.sleep(forTimeInterval: 0.002)
        }

        var pixelBuffer: CVPixelBuffer?
        let status: CVReturn
        if let pool = adaptor.pixelBufferPool {
            status = CVPixelBufferPoolCreatePixelBuffer(
                kCFAllocatorDefault,
                pool,
                &pixelBuffer
            )
        } else {
            status = CVPixelBufferCreate(
                kCFAllocatorDefault,
                width,
                height,
                kCVPixelFormatType_32BGRA,
                [
                    kCVPixelBufferPixelFormatTypeKey as String: Int(
                        kCVPixelFormatType_32BGRA
                    ),
                ] as CFDictionary,
                &pixelBuffer
            )
        }
        guard status == kCVReturnSuccess, let buffer = pixelBuffer else {
            throw VideoEncoderError.cannotCreatePixelBuffer
        }

        CVPixelBufferLockBaseAddress(buffer, [])
        defer {
            CVPixelBufferUnlockBaseAddress(buffer, [])
        }
        guard let baseAddress = CVPixelBufferGetBaseAddress(buffer) else {
            throw VideoEncoderError.cannotCreatePixelBuffer
        }

        let destinationRowBytes = CVPixelBufferGetBytesPerRow(buffer)
        for y in 0..<height {
            let sourceRow = y * image.bytesPerRow
            let destination = baseAddress
                .advanced(by: y * destinationRowBytes)
                .assumingMemoryBound(to: UInt8.self)
            for x in 0..<width {
                let source = sourceRow + x * 4
                destination[x * 4] = image.pixels[source + 2]
                destination[x * 4 + 1] = image.pixels[source + 1]
                destination[x * 4 + 2] = image.pixels[source]
                destination[x * 4 + 3] = image.pixels[source + 3]
            }
        }

        let presentationTime = CMTime(
            value: frameIndex,
            timescale: CMTimeScale(frameRate)
        )
        guard adaptor.append(buffer, withPresentationTime: presentationTime) else {
            throw VideoEncoderError.appendFailed(
                writer.error?.localizedDescription ?? "append failed"
            )
        }
        frameIndex += 1
    }

    public func finish() async throws {
        guard !didFinish else { return }
        guard writer.status == .writing else {
            throw VideoEncoderError.finishFailed(
                writer.error?.localizedDescription ?? "writer is not writing"
            )
        }
        didFinish = true
        input.markAsFinished()
        await withCheckedContinuation { continuation in
            writer.finishWriting {
                continuation.resume()
            }
        }
        guard writer.status == .completed else {
            throw VideoEncoderError.finishFailed(
                writer.error?.localizedDescription ?? "writer did not complete"
            )
        }
    }

    public func cancel() {
        didFinish = true
        writer.cancelWriting()
    }
}
