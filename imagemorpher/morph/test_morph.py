import skimage as sk
import pdb
import numpy as np
from django.test import TestCase
import skimage.io as skio
from morph.morph import morph
from skimage.measure import compare_ssim as ssim
from autocrop import Cropper

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

# Test for the morph algorithm correctness by minimizing image differences
# and validating the SSIM
class MorphTestCorrectness(TestCase):
    def test_get_morphed_img(self):
        self.assertEqual(True, True)

    def testMorphs(self):
      cropper = Cropper()
      img1 = skio.imread('morph/content/images/correctness/george_small.jpg')
      img2 = skio.imread('morph/content/images/correctness/obama_small.jpg')
      img1 = cropper.crop('morph/content/images/correctness/george_small.jpg')
      img2 = cropper.crop('morph/content/images/correctness/obama_small.jpg')
      morphed_img = morph(img1, img2, 0.5)
      expectedMorphedImg = skio.imread('morph/content/images/correctness/george_obama_small.jpg')
      ssim = ssim(img1, img2)   # @TODO: Blocked by images having different dimensions
      return np.array_equal(morphed_im, expectedMorphedImg)
        
      return False
