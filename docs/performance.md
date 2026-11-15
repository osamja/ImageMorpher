# Performance

Goal: make morphs fast enough that long sequences don't dominate worker time,
and make a single morph cheap enough to keep p95 latency low.

## What was slow

1. `getDetectedCorrespondingPoints()` constructed the dlib detector and loaded
   the 96 MB `shape_predictor_68_face_landmarks.dat` on every call. `morph()`
   called it once per image, and `processMorph()` called `morph()` once per
   frame. A 101-frame sequence therefore loaded/parsed the model 202 times.
2. `tasks.py` wrote every frame to disk as a JPEG, then reopened every JPEG to
   assemble the GIF.
3. `getTriPoints()` built a Python tuple for every pixel of every image and
   asked `Delaunay.find_simplex` to classify the whole grid, for every frame.
4. `tasks.py` copied both images for every frame even though the morph code
   does not mutate its inputs.
5. `matplotlib` was imported on the production path even though it is only
   used by the old interactive point-picking helper.

## What changed

- `morph/utils/detection.py` keeps one detector and one shape predictor per
  process, behind a lock. Detection is serialized because Dramatiq uses
  threads and dlib's detector is not documented as thread-safe.
- `processMorph()` detects both faces once, then passes the 68-point landmark
  arrays into every `morph()` call.
- `tasks.py` keeps the morphed frames as PIL images in memory and builds the
  GIF from those images. Intermediate JPEGs are still written because the
  status endpoint exposes them via `intermediateImages`.
- GIF frames are pre-quantized with `Image.FASTOCTREE`. The old per-frame
  median-cut path spent ~13 s and produced a ~12 MB GIF for 101 frames; the
  fast path is ~1.3 s and ~7 MB. Set `MORPH_GIF_QUANTIZE=quality` to restore
  the slower, slightly higher-fidelity path.
- `morph_frame()` supports a `legacy` and a `vectorized` warp implementation.
  The vectorized path walks each triangle's bounding box, solves barycentric
  coordinates, and samples the source image. It does not build a full-image
  pixel grid or call `find_simplex`.
- `morph.py` no longer imports matplotlib, `pdb`, or `skimage` on the
  production path, and the hardcoded `/app/imagemorpher/morph` `sys.path`
  entries are gone.

## Rollback switch

`MORPH_WARP_IMPL=legacy` restores the old warp math without a code revert.
The default is `vectorized`. Restart the API and worker after changing it.

## Benchmark

Run this in the API container (or any container with the app dependencies):

```bash
python manage.py benchmark_morph --frames 1,6,101 --repeat 3 --warp vectorized
```

To compare against the old implementation:

```bash
python manage.py benchmark_morph --frames 1,6,101 --repeat 3 --warp both
```

The command crops the fixture images once, detects landmarks once, warms the
caches, and reports mean/min seconds and frames per second. It does not write
morph output files.

Measured on the `face-1.jpeg` / `face-2.jpeg` fixture pair at 500×500:

| frames | legacy warp | vectorized warp |
|---:|---:|---:|
| 1 | 0.487 s | 0.091 s |
| 6 | 2.972 s | 0.586 s |
| 101 | 52.063 s | 9.566 s |

Those numbers pass the same pre-detected landmarks into every frame. The old
production path also reloaded the 96 MB model and re-detected once per frame,
so the real before/after gap is larger than the warp-only table.

End-to-end `processMorph` for 101 frames, including the 101 intermediate JPEG
writes and GIF encoding, took **12.76 s** in the same container and produced a
6.9 MB GIF. Record updated numbers here when running on the worker hardware.
