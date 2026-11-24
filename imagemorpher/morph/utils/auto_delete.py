"""Remove cloud image uploads and morphs after 30 days."""

import argparse
from pathlib import Path
import stat
import time


IMAGE_DIRECTORY = Path(__file__).resolve().parents[1] / "content" / "temp_morphed_images"
RETENTION_SECONDS = 30 * 24 * 60 * 60
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".gif", ".png", ".heic", ".heif", ".webp"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delete", action="store_true", help="Delete eligible files")
    args = parser.parse_args()
    cutoff = time.time() - RETENTION_SECONDS
    count = 0

    for path in IMAGE_DIRECTORY.iterdir():
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        try:
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_mtime >= cutoff:
                continue
            if args.delete:
                path.unlink()
            count += 1
        except FileNotFoundError:
            continue

    action = "Deleted" if args.delete else "Eligible for deletion:"
    print(f"{action} {count} image files older than 30 days.")


if __name__ == "__main__":
    main()
