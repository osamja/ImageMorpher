from django.test import TestCase
import imagehash
from PIL import Image
import cv2
from autocrop import Cropper

from morph.morph import morph
from morph.utils.graphics import getImageReadyForCrop, getCroppedImagePath
from morph.exceptions.CropException import CropException

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

2. Test morph algorithm performance
"""


def getFormattedImages(img1_path, img2_path):
    """
    Crop the two input images to their faces and return them as in-memory
    numpy arrays, matching the original morph preprocessing step.
    """
    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)

    cropper = Cropper()

    img1 = getImageReadyForCrop(img1)
    img2 = getImageReadyForCrop(img2)

    img1_cropped = cropper.crop(img1)
    img2_cropped = cropper.crop(img2)

    img1_cropped_cv = cv2.cvtColor(img1_cropped, cv2.COLOR_BGR2RGB)
    img2_cropped_cv = cv2.cvtColor(img2_cropped, cv2.COLOR_BGR2RGB)

    return img1_cropped_cv, img2_cropped_cv


def getExceptionTestCases():
    test_cases = {
        "iphoneSelfie": {
            "input": [
                'morph/tests/content/input/sammy-selfie.HEIC',
                'morph/tests/content/input/zuby.jpg',
            ],
            "expected": [
                'Image file type is not supported',
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

            _, morphed_img = morph(img1, img2, 0.5)
            morphed_image = Image.fromarray(morphed_img)
            morphed_image = morphed_image.convert("RGB")
            hash1 = imagehash.average_hash(morphed_image)
            hash0 = imagehash.average_hash(Image.open(output_path))
            imageSimilarityTolerance = 5
            print('Test: ', test_case)
            imgDifference = abs(hash1 - hash0)
            areImagesSimilar = imgDifference < imageSimilarityTolerance
            self.assertTrue(
                areImagesSimilar,
                f'{test_case} hash difference {imgDifference} >= {imageSimilarityTolerance}'
            )

    def testMorphExceptionHandling(self):
        """
        Test that the morph algorithm throws helpful exceptions where input is unsupported
        """
        test_cases = getExceptionTestCases()

        for test_case in test_cases:
            current_test = test_cases[test_case]
            img1_path = current_test['input'][0]

            with self.assertRaises(CropException):
                getCroppedImagePath(img1_path)
