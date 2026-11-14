# ImageMorpher — Native Swift (Client-Side) Rewrite

## Goal

Rewrite ImageMorpher to run entirely on-device in Swift, replacing the
React Native client + Django/Python backend. No server round-trip for the
morph itself; everything (face detection, triangulation, warping, encoding)
happens on the device.

## Decisions (confirmed)

| Decision | Choice |
|---|---|
| Sequence output | Video (H.264/HEVC via AVAssetWriter); still images for single-frame morphs |
| Delaunay triangulation | Pure Swift, hand-written Bowyer–Watson |
| Platform scope | iOS only, fully anonymous/offline (SwiftData history, no accounts) |

## Current state → target

Today (server-side):

```
React Native client
  → POST /morph/upload (two images)
  → autocrop (OpenCV Haar + dlib fallback)
  → dlib 68-point landmarks
  → Dramatiq worker: scipy Delaunay + numpy affine warp + cross-dissolve
  → PIL GIF assembly
  → client polls /morph/status/<uuid>, downloads result
```

Target: every step moves on-device. The core algorithm is conceptually
identical; it is a mapping of Python libs → Apple frameworks.

---

## Architecture

Two targets: a reusable, UI-free **SwiftPM library** (`MorpherCore`) and a
thin **SwiftUI app**.

```
ios/
├── MorpherCore/                     # SwiftPM library — all logic, no UI
│   ├── Package.swift
│   ├── Sources/MorpherCore/
│   │   ├── Image/
│   │   │   ├── ImageBuffer.swift     # raw RGBA pixel buffer (w/h + bytes)
│   │   │   └── ImageLoader.swift     # downsample-safe decode (CGImageSource thumbnail)
│   │   ├── Face/
│   │   │   ├── FaceDetector.swift    # Vision VNDetectFaceLandmarksRequest wrapper
│   │   │   ├── Landmarks.swift       # fixed-order [SIMD2<Double>] + corner points
│   │   │   └── FaceCropper.swift     # crop+align around face, scale to canonical size
│   │   ├── Geometry/
│   │   │   ├── Triangle.swift
│   │   │   ├── Delaunay.swift        # Bowyer–Watson
│   │   │   └── Barycentric.swift     # point-in-triangle + affine mapping (SIMD)
│   │   ├── Warp/
│   │   │   ├── AffineWarp.swift      # per-triangle inverse warp
│   │   │   └── Dissolve.swift        # (1-t)*A + t*B
│   │   ├── Morph/
│   │   │   ├── Morpher.swift         # morph(img1, img2, t) -> ImageBuffer
│   │   │   └── SequenceGenerator.swift # loop t, TaskGroup, AsyncStream progress
│   │   └── Output/
│   │       ├── VideoEncoder.swift    # AVAssetWriter H.264/HEVC
│   │       └── StillExporter.swift   # CGImage
│   └── Tests/MorpherCoreTests/       # parity + unit tests
├── ImageMorpher.xcodeproj
├── ImageMorpher.xcworkspace          # references app + local MorpherCore package
├── ImageMorpher/                     # SwiftUI sources
├── ImageMorpherTests/
└── ImageMorpherUITests/
```

### App (SwiftUI)

- `PhotosPicker` → live frame-animation preview → progress → `ShareLink` /
  save to Photos.
- `HistoryStore` (SwiftData), local-only, no auth.

---

## Framework mapping (Python → Swift)

| Current (Python) | Swift equivalent |
|---|---|
| dlib frontal detector + `shape_predictor_68` | **Vision** `VNDetectFaceLandmarksRequest` (bundled with iOS) |
| autocrop (OpenCV Haar) + dlib fallback | Vision face bounding box + `roll`, crop w/ padding, scale to 500×500 (CoreGraphics) |
| scipy `Delaunay` | **Hand-written Bowyer–Watson** (see below) |
| numpy affine / `pinv` / `find_simplex` | `simd_double3x3` + barycentric coordinates, `Accelerate` |
| matplotlib `ginput` | SwiftUI `Canvas` + `DragGesture` |
| PIL GIF assembly | ImageIO `CGImageDestination` (if GIF ever needed) / `AVAssetWriter` |
| Dramatiq + Redis + Postgres | Nothing — on-device concurrency |

---

## Core pipeline (per frame)

1. Decode both images as downsampled thumbnails (cap ~600×600).
2. Detect faces + landmarks on each; error if none found.
3. Build a **fixed-order** landmark array (Vision regions assembled into a
   stable ordering) + 4 corner points. Ordering must match across both images.
4. Midpoints `Pm = (1−t)·P1 + t·P2`.
5. Delaunay-triangulate `Pm`.
6. For each triangle, inverse-warp each source to `Pm` via barycentric
   coordinates (solve `p = αA+βB+γC`, sample `q = αA'+βB'+γC'`).
7. Cross-dissolve: `out = (1−t)·warp1 + t·warp2`.
8. Encode the frame.

---

## The two hard problems

### 1. Delaunay triangulation (no built-in API)

**Chosen: pure-Swift Bowyer–Watson** (~200–300 lines), super-triangle +
robust `orient2d`, standard circumcircle test. ~73 points is trivial.

Parity-test against `scipy.spatial.Delaunay` by dumping expected simplex sets
to JSON fixtures and asserting identical triangulation.

### 2. Vision landmark correspondence

dlib gives exactly 68 always-present points; Vision gives *optional* regions
and a different count. Need a mapping layer that:
- orders Vision's regions into a stable array,
- fills/omits missing regions deterministically,
- validates the count matches across the two images (mirrors `resizePts`
  trimming today).

This is the correctness gate for the whole feature — lock it down with tests
before building on top of it.

---

## Concurrency & performance

- Frames are embarrassingly parallel → `withThrowingTaskGroup` with bounded
  concurrency (~ `activeProcessorCount`).
- Progress via `AsyncStream<Int>` (mirrors the existing `progress` field).
- CPU + SIMD/Accelerate is sufficient for 500×500 × 2 warps × ≤101 frames.
- **Metal compute** (one thread per output pixel) is the v2 optimization;
  keep `Warp` behind a protocol so a GPU backend can slot in later.

## Output

- Sequence → `AVAssetWriter` (`AVAssetWriterInputPixelBufferAdaptor`),
  HEVC with H.264 fallback, `kCVPixelFormatType_32BGRA`.
- In-app preview animates frame buffers directly (no encode until share/save).
- Single-frame → still `CGImage` via `StillExporter`.
- GIF only if parity with the old server URLs is ever required (ImageIO
  `CGImageDestination`).

---

## Build order (milestones)

1. **`ImageBuffer` + loader + cropper** — decode, crop around Vision face,
   scale to canonical 500×500. (Replaces `graphics.py` autocrop + dlib fallback.)
2. **`FaceDetector` + `Landmarks`** — Vision wrapper, stable ordering, corners,
   no-face error. *Fiddliest part; test first.*
3. **`Delaunay` + `Barycentric`** — parity-test against scipy fixtures.
4. **`AffineWarp` + `Dissolve` + `Morpher`** — single frame at `t`; correctness
   test mirroring `test_morph_correctness.py` (assert against a known expected
   image at `t=0.5`).
5. **`SequenceGenerator` + `VideoEncoder`** — parallel frames, progress stream,
   HEVC encode.
6. **SwiftUI app** — picker, live preview, progress, share/save, SwiftData history.

---

## Testing strategy

- **Parity:** keep Python `morph.py` as a reference oracle; dump its
  intermediate outputs (landmarks, Delaunay triangles, warped frames) as
  fixtures and assert the Swift pipeline reproduces them.
- **Unit:** Delaunay (degenerate/collinear points), barycentric, dissolve,
  landmark ordering.
- **Correctness:** image-equality assertion at `t=0.5` (existing
  `test_morph_correctness.py` pattern).
- Do not delete the Python backend during the port.

---

## Repository management

The Swift code lands in the **same repository** (`osamja/ImageMorpher`),
alongside the untouched Python backend.

### Layout

Python stays at the root; Swift goes under `ios/`. See architecture tree above.

### Files to touch

1. **`.gitignore`** — append Xcode/SwiftPM noise:
   ```gitignore
   .DS_Store
   DerivedData/
   build/
   *.xcuserstate
   xcuserdata/
   .swiftpm/
   ios/MorpherCore/Package.resolved   # ignore for the library package
   ```

2. **`.dockerignore`** — keep the Docker build context lean:
   ```dockerignore
   ios/
   ```

3. **`.github/workflows/ci.yml`** — path-filter so Swift-only commits don't
   trigger Python test → Docker build → Linode deploy:
   ```yaml
   on:
     push:
       branches: [master]
       paths-ignore: ['ios/**', 'docs/**']
     pull_request:
       branches: [master]
       paths-ignore: ['ios/**', 'docs/**']
   ```

4. **`.github/workflows/ci-swift.yml`** (new) — macOS runner, simulator
   destination (no code signing):
   ```yaml
   on:
     push:     { branches: [master], paths: ['ios/**'] }
     pull_request: { branches: [master], paths: ['ios/**'] }
   jobs:
     test:
       runs-on: macos-14
       steps:
         - uses: actions/checkout@v4
         - uses: maxim-lobanov/setup-xcode@v1
           with: { xcode-version: '15.4' }
         - run: swift test
           working-directory: ios/MorpherCore
         - run: >
             xcodebuild test -scheme ImageMorpher
             -destination 'platform=iOS Simulator,name=iPhone 15'
           working-directory: ios
   ```

### Branching strategy

**Feature branch** (recommended): `ios/swift-rewrite` → merge to `master`
when shippable. Matches the repo's existing feature-branch habit and keeps
`master` = "what's live on pyaar.ai."

```bash
git checkout master && git pull
git checkout -b ios/swift-rewrite
git add ios/ .gitignore .dockerignore .github/workflows
git commit -m "feat(ios): add native Swift image morpher (core + app)"
git push -u origin ios/swift-rewrite
```

Alternative: straight to `master` (viable only because the code is additive
and CI path filters stop Swift commits from redeploying Python).

### Versioning

- Python API keeps its existing `release/vX.Y.Z` branches + Docker image tags.
- Swift app versions via Xcode `MARKETING_VERSION` (start `0.1.0`); tag the
  first shippable build `ios-v0.1.0` rather than reusing API version numbers.

### CI gotcha

The existing `build-push` + `deploy` + `health-check` jobs fire on every push
to `master`. Without the `paths-ignore` filter, every Swift commit would
rebuild and redeploy the Python API to Linode unnecessarily.

---

## Risks

- **Vision landmark correspondence** — the correctness gate for the whole feature.
- **Delaunay robustness** — degenerate/collinear points from Vision.
- **Video memory** — 101 frames × 500×500 RGBA ≈ 100 MB peak; bound concurrency,
  reuse pixel buffers.
- **Parity drift** — keep Python `morph.py` as the oracle during the port.
- **Code signing** — CI uses simulator (unsigned); device/TestFlight signing
  configured locally, not in CI.
