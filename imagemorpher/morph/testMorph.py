import skimage as sk
import pdb
import numpy as np

def testMorphs(img1_name, img2_name, morphed_im):
  # pdb.set_trace()
  if (img1_name == 'adele_small' and img2_name == 'tiger_small'):
    expectedMorphedImg = sk.io.imread('adele_tiger_small_.png')
    return np.array_equal(morphed_im, expectedMorphedImg)
  return False
