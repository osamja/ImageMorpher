import skimage.io as skio
from django.test import TestCase
from .main_morph import morph
import pdb

# Create your tests here.
class MorphTest(TestCase):
    def test_get_morphed_img(self):
        self.assertEqual(True, True)

    def test_morph(self):
        pdb.set_trace()
        img1 = skio.imread('morph/images/obama_small.jpg')
        img2 = skio.imread('morph/images/george_small.jpg')
        morphed_img_uri = morph(img1, img2, 0.5)
