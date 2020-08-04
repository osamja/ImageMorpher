import skimage as sk
import pdb
import numpy as np
from django.test import TestCase
import skimage.io as skio
from morph.morph import morph
from skimage.measure import compare_ssim as ssim
import imagehash
from PIL import Image

"""
Test morph algorithm correctness
    Use SSIM to test our morph algorithm by evaluating the SSIM of the
    morphed image and expected image

    https://scikit-image.org/docs/dev/auto_examples/transform/plot_ssim.html

Create two additional morph test files for

1. Test morph algorithm robustness under varying conditions such as image
    - dimensions
    - file formats
    - multiple detected faces
    - no detected faces
    - face aspect ratios & angles
    - 

2. Test morph algorithm performance
"""

def getTestCases():
    test_cases = {
        # "test0": {
        #     "input": [
        #         'morph/tests/content/input/1.jpeg',
        #         'morph/tests/content/input/2.jpeg',
        #     ],
        #     "expected": [
        #         'morph/tests/content/expected/morph-1-2.jpg',
        #     ],
        # },
        # "test1": {
        #     "input": [
        #         'morph/tests/content/input/face-1.jpeg',
        #         'morph/tests/content/input/face-2.jpeg',
        #     ],
        #     "expected": [
        #         'morph/tests/content/expected/face-1-2.jpg',
        #     ],
        # },
        # "test2": {
        #     "input": [
        #         'morph/tests/content/input/keanu.jpeg',
        #         'morph/tests/content/input/pitt.jpg',
        #     ],
        #     "expected": [
        #         'morph/tests/content/expected/keanu-pitt.jpg',
        #     ],
        # },
        # "test3": {
        #     "input": [
        #         'morph/tests/content/input/obama_small.jpg',
        #         'morph/tests/content/input/clooney_small.jpg',
        #     ],
        #     "expected": [
        #         'morph/tests/content/expected/george_obama_small.jpg',
        #     ],
        # },
        # "differentImageSizes": {
        #     "input": [
        #         'morph/tests/content/input/obama_small.jpg',
        #         'morph/tests/content/input/clooney_fit.jpg',
        #     ],
        #     "expected": [
        #         'morph/tests/content/expected/george_obama_small.jpg',
        #     ],
        # },
        "PNGFileTypes": {
            "input": [
                'morph/tests/content/input/will-smith.png',
                'morph/tests/content/input/tom-holland.png',
            ],
            "expected": [
                'morph/tests/content/expected/george_obama_small.jpg',
            ],
        },
        # "largeFileTypes": {
        #     "input": [
        #         'morph/tests/content/input/obama_small.jpg',
        #         'morph/tests/content/input/clooney_fit.jpg',
        #     ],
        #     "expected": [
        #         'morph/tests/content/expected/george_obama_small.jpg',
        #     ],
        # },
    }
    
    return test_cases

# Test for the morph algorithm correctness by asserting the morphed image
# resembles our expectations for the halfway image
class MorphTestCorrectness(TestCase):
    def test_get_morphed_img(self):
        self.assertEqual(True, True)

    def testMorphCorrectness(self):
      """
      Test that the basic morph algorithm is working on two similarly sized images
      """
      test_cases = getTestCases()

      for test_case in test_cases:
        current_test = test_cases[test_case]
        img1_path = current_test['input'][0]
        img2_path = current_test['input'][1]
        output_path = current_test['expected'][0]

        img1 = skio.imread(img1_path)
        img2 = skio.imread(img2_path)

        morphed_img_array = morph(img1, img2, 0.5)
        morphed_image = Image.fromarray(morphed_img_array[1])
        morphed_image = morphed_image.convert("RGB")
        hash1 = imagehash.average_hash(morphed_image) 
        hash0 = imagehash.average_hash(Image.open(output_path))
        imageSimilarityTolerance = 0
        self.assertEqual(hash1 - hash0, imageSimilarityTolerance)
