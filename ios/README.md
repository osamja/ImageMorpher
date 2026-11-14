# ImageMorpher — Native Swift (iOS)

Client-side rewrite of ImageMorpher, entirely in Swift. The morph algorithm
(face landmarks → Delaunay triangulation → per-triangle inverse warp →
cross-dissolve) runs on-device, with no server round-trip.

See the architecture and milestones in [`docs/swift-rewrite.md`](../docs/swift-rewrite.md).

## Layout

```
ios/
├── MorpherCore/                 # SwiftPM library — pure Swift, no UI, platform-agnostic
│   ├── Sources/MorpherCore/     # ImageBuffer, Delaunay, Barycentric, AffineWarp,
│   │                            # Dissolve, Morpher, SequenceGenerator, PPMImage, FaceDetector
│   ├── Sources/morpher-demo/    # CLI demo: morph two synthetic images → PPM frames
│   ├── Tests/MorpherCoreTests/  # unit + scipy parity tests
│   └── scripts/                 # regenerates the scipy Delaunay parity fixture
└── (app target — to be added)   # SwiftUI + Vision + AVAssetWriter (Apple platforms only)
```

`MorpherCore` deliberately imports **no Apple frameworks** (no Vision, no
CoreGraphics, no AVFoundation). Face detection is behind the `FaceDetector`
protocol and images use a plain RGBA `ImageBuffer` (PPM for files on Linux,
`CGImage` on Apple platforms). That keeps the entire algorithmic core buildable
and testable on Linux, while the Apple-specific pieces live in the app layer.

## Build & test

### Linux (Docker)

```bash
# Run the unit + parity test suite
docker run --rm -v "$PWD/MorpherCore":/src -w /src swift:6.0 swift test

# Run the demo (writes PPM frames)
docker run --rm -v "$PWD/MorpherCore":/src -v /tmp:/tmp -w /src \
  swift:6.0 swift run -c release morpher-demo /tmp/morph-demo
```

### macOS / iOS

```bash
cd ios/MorpherCore
swift test                      # MorpherCore unit + parity tests
```

The iOS app (Vision face detection, AVAssetWriter video output, SwiftUI UI)
lives in a separate Xcode project/workspace and requires macOS to build.

## Testing strategy

- **Unit tests** cover Delaunay, barycentric coordinates, affine warp, dissolve,
  and the full `morph` operation (identity, endpoints, midpoint, sequence).
- **Parity tests** assert the Swift Bowyer–Watson triangulation exactly matches
  `scipy.spatial.Delaunay` on a fixed point set. The fixture
  (`Tests/MorpherCoreTests/ParityFixture.swift`) is regenerated from the Python
  reference with:

  ```bash
  docker run --rm --entrypoint python3 \
    -v "$PWD/MorpherCore":/src ghcr.io/osamja/face-morpher-api \
    /src/scripts/gen_delaunay_fixture.py > \
    "$PWD/MorpherCore/Tests/MorpherCoreTests/ParityFixture.swift"
  ```
