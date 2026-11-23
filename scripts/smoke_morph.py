"""Exercise the deployed upload, async morph, legacy polling, and image download."""
import argparse
import io
import time
from pathlib import Path
from uuid import UUID

import requests
from PIL import Image

FIXTURES = (
    Path(__file__).resolve().parents[1] / "imagemorpher/morph/tests/content/input"
)
LEGACY_AGENT = "MyMorph/1.0 CFNetwork"


def check_response(response):
    if response.status_code != 200:
        raise RuntimeError(f"{response.request.method} {response.url}: HTTP {response.status_code}")
    return response


def run_smoke_test(base_url, poll_timeout):
    base_url = base_url.rstrip("/")
    with requests.Session() as session:
        check_response(session.get(f"{base_url}/morph/", timeout=10))

        refs = []
        for filename in ("face-1.jpeg", "face-2.jpeg"):
            with (FIXTURES / filename).open("rb") as fixture:
                response = check_response(session.post(
                    f"{base_url}/morph/upload",
                    files={"firstImageRef": (filename, fixture, "image/jpeg")},
                    timeout=20,
                ))
            ref = response.json()
            if not isinstance(ref, str) or not ref:
                raise RuntimeError(f"Upload of {filename} did not return an image reference")
            refs.append(ref)

        started = time.monotonic()
        response = check_response(session.post(
            f"{base_url}/morph",
            data={
                "firstImageRef": refs[0],
                "secondImageRef": refs[1],
                "isAsync": "True",
                "isSequence": "True",
                "stepSize": "50",
                "clientId": "deploy-smoke",
            },
            timeout=15,
        ))
        morph_id = UUID(response.json()["morphId"])
        print(f"Submitted morph {morph_id}", flush=True)

        deadline = time.monotonic() + poll_timeout
        status = "unknown"
        while (remaining := deadline - time.monotonic()) > 0:
            response = check_response(session.get(
                f"{base_url}/morph/status/{morph_id}/",
                headers={"User-Agent": LEGACY_AGENT},
                timeout=min(10, remaining),
            ))
            result = response.json()
            status = result["status"]
            if status == "complete":
                break
            if status not in {"pending", "processing"}:
                raise RuntimeError(f"Morph {morph_id} returned legacy-client status {status!r}")
            time.sleep(max(0, min(1, deadline - time.monotonic())))
        else:
            raise RuntimeError(f"Morph {morph_id} timed out with status {status!r}")

        if result["progress"] != 100:
            raise RuntimeError(f"Morph {morph_id} completed with incomplete progress")
        response = check_response(session.get(result["morphUri"], timeout=15))
        with Image.open(io.BytesIO(response.content)) as image:
            if image.format != "GIF" or not image.is_animated:
                raise RuntimeError(f"Morph {morph_id} did not return an animated GIF")
            for frame in range(image.n_frames):
                image.seek(frame)
                image.load()
            print(f"Morph {morph_id} decoded at {image.width}×{image.height} "
                  f"in {time.monotonic() - started:.2f}s from submission")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="Public origin, for example https://pyaar.ai")
    parser.add_argument("--poll-timeout", type=float, default=60)
    args = parser.parse_args()
    try:
        run_smoke_test(args.base_url, args.poll_timeout)
    except (requests.RequestException, RuntimeError, ValueError, KeyError, OSError) as exc:
        parser.exit(1, f"Smoke test failed: {exc}\n")


if __name__ == "__main__":
    main()
