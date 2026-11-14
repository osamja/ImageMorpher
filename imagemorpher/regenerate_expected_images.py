"""One-off helper to re-baseline the morph correctness test's expected images.

Run from the `imagemorpher` directory with Django configured. For each test
case it runs the exact same crop + morph pipeline the test uses and overwrites
the committed expected image, so the test reflects the current dependency stack
(e.g. autocrop 2.x / YuNet face detector).
"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'imagemorpher.settings')
os.environ.setdefault('SECRET_KEY', 'ci-test-key')

import django  # noqa: E402

django.setup()

from PIL import Image  # noqa: E402

from morph.morph import morph  # noqa: E402
from morph.tests.correctness.test_morph_correctness import (  # noqa: E402
    getFormattedImages,
    getTestCases,
)


def main():
    for name, case in getTestCases().items():
        img1_path = case['input'][0]
        img2_path = case['input'][1]
        output_path = case['expected'][0]

        print(f'Regenerating {name}: {img1_path} + {img2_path} -> {output_path}')
        img1, img2 = getFormattedImages(img1_path, img2_path)
        _, morphed_img = morph(img1, img2, 0.5)
        Image.fromarray(morphed_img).convert('RGB').save(output_path)
        print(f'  wrote {output_path}')


if __name__ == '__main__':
    main()
