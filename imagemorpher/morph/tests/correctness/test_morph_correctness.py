import skimage as sk
import pdb
import numpy as np
from django.test import TestCase
import skimage.io as skio
from morph.morph import morph
from skimage.measure import compare_ssim as ssim
import imagehash
from PIL import Image
from utils.graphics import getFormattedImages

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

def getExceptionTestCases():
    test_cases = {
        "iphoneSelfie": {
            "input": [
                'morph/tests/content/input/sammy-selfie.HEIC',
                'morph/tests/content/input/zuby.jpg',
            ],
            "expected": [
                ValueError('Image file type is not supported'),
            ],
        },
    }

    return test_cases

def getTestCases():
    test_cases = {
        "quickSanityTest": {
            "input": [
                'morph/tests/content/input/1.jpeg',
                'morph/tests/content/input/2.jpeg',
            ],
            "expected": [
                'morph/tests/content/expected/morph-1-2.jpg',
            ],
        },
        "test1": {
            "input": [
                'morph/tests/content/input/face-1.jpeg',
                'morph/tests/content/input/face-2.jpeg',
            ],
            "expected": [
                'morph/tests/content/expected/face-1-2.jpg',
            ],
        },
        "test2": {
            "input": [
                'morph/tests/content/input/keanu.jpeg',
                'morph/tests/content/input/pitt.jpg',
            ],
            "expected": [
                'morph/tests/content/expected/keanu-pitt.jpg',
            ],
        },
        "test3": {
            "input": [
                'morph/tests/content/input/obama_small.jpg',
                'morph/tests/content/input/clooney_small.jpg',
            ],
            "expected": [
                'morph/tests/content/expected/george_obama_small.jpg',
            ],
        },
        "differentImageSizes": {
            "input": [
                'morph/tests/content/input/obama_small.jpg',
                'morph/tests/content/input/clooney_fit.jpg',
            ],
            "expected": [
                'morph/tests/content/expected/george_clooney_obama_resized_cropped.jpg',
            ],
        },
        "PNGFileTypes": {
            "input": [
                'morph/tests/content/input/will-smith.png',
                'morph/tests/content/input/tom-holland.png',
            ],
            "expected": [
                'morph/tests/content/expected/will-smith-tom-holland.jpg',
            ],
        },
        "largeFileTypes": {
            "input": [
                'morph/tests/content/input/bill-hader-large.jpg',
                'morph/tests/content/input/fred-armisan-large.jpg',
            ],
            "expected": [
                'morph/tests/content/expected/bill-hader-fred-armisan-large.jpg',
            ],
        },
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
        img1, img2 = getFormattedImages(img1_path, img2_path)
        # img1, img2 = getSimilarSizedImages(img1, img2)

        morphed_img_array = morph(img1, img2, 0.5)
        morphed_image = Image.fromarray(morphed_img_array[1])
        morphed_image = morphed_image.convert("RGB")
        hash1 = imagehash.average_hash(morphed_image) 
        hash0 = imagehash.average_hash(Image.open(output_path))
        imageSimilarityTolerance = 5
        print('Test: ', test_case)
        imgDifference = abs(hash1 - hash0)
        areImagesSimilar = imgDifference < imageSimilarityTolerance
        self.assertEqual(areImagesSimilar, True)

    def testMorphExceptionHandling(self):
        """
        Test that the morph algorithm throws helpful exceptions where input is unsupported
        """
        test_cases = getExceptionTestCases()

        for test_case in test_cases:
            current_test = test_cases[test_case]
            img1_path = current_test['input'][0]
            img2_path = current_test['input'][1]

            # Option 1 for testing exceptions
            try:
                img1, img2 = getFormattedImages(img1_path, img2_path)
                self.fail('Expected image file type exception to be thrown')
            except ValueError:
                pass

            # Option 2 for testing exceptions
            with self.assertRaises(ValueError):
                img1, img2 = getFormattedImages(img1_path, img2_path)
