import skimage as sk
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay
from skimage.transform import resize
import time
import imageio
import dlib
import pdb
import datetime
import uuid
from dotenv import load_dotenv
load_dotenv()
import sys
# morph is essentially the src root directory in this file now
#   aka import all files with morph/<file-path>
sys.path.insert(0, '/app/imagemorpher/morph')
from utils.image_sources import getImages, getCorrespondingPts, addCornerPoints

import logging
logging.basicConfig(filename='morph/logs/morph-app-perf.log', level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

"""
Image Morphing
We know how to warp one image into the other, but
how do we create a morphing sequence?-
1. Create an intermediate shape (by interpolation)
2. Warp both images towards it
3. Cross-dissolve the colors in the newly warped images
"""

def getDetectedCorrespondingPoints(img):
  detector = dlib.get_frontal_face_detector()
  predictor = dlib.shape_predictor('morph/utils/shape_predictor_68_face_landmarks.dat')
  # logging.info('detector: ', detector)
  # pdb.set_trace()
  try:
    face = detector(img, 1)[0]      # get first face
  except Exception as e:
    # ideally here, we return this in the HTTP Response
    logging.error("Could not find corresponding points..")
    raise
  face_detection_object = predictor(img, face)
  face_points = face_detection_object.parts()
  landmarks = np.array([[p.x, p.y] for p in face_points])
  landmarks = addCornerPointsOnImg(img, landmarks)
  return landmarks

def addCornerPointsOnImg(im1, pts):
  minW, minH = 0, 0
  maxW, maxH = im1.shape[1], im1.shape[0]
  pts = np.append(pts, np.array([minW, minH]).reshape((1,2)), axis=0)
  pts = np.append(pts, np.array([minW, maxH]).reshape((1,2)), axis=0)
  pts = np.append(pts, np.array([maxW, minH]).reshape((1,2)), axis=0)
  pts = np.append(pts, np.array([maxW, maxH]).reshape((1,2)), axis=0)
  return pts

# Cross Disolve between two images (set of pts) at time t
#  e.g. Image(halfway t:0.5) = (1 - t) * Image_1 + t * Image_2 wh
def crossDisolve(pts1, pts2, t, isImage=True):

  ### Ensure images are same size, else resize them to be scaling up if necessary
  if (isImage):
    if (pts1.shape != pts2.shape):
      # pdb.set_trace()
      new_shape = min(pts1.shape, pts2.shape)
      pts1 = np.resize(pts1, new_shape) #resize(pts1, bigger_shape)
      pts2 = np.resize(pts2, new_shape) #resize(pts2, bigger_shape)
  ###

  first_image = (1-t) * pts1
  second_image = (t) * pts2
  if (isImage):
    dissolveImg = np.add(first_image.astype(np.uint8), second_image.astype(np.uint8))
  else:
    dissolveImg = np.add(first_image, second_image)
  return dissolveImg

def getTriPoints(im1, tri):
  """
  Map every point/pixel in im1 to its corresponding triangle

  data structure:  {tri_num: [pixels belonging to cur_tri]}
  """
  tri_dict = {}
  
  grid_points = np.asarray([(x, y) for y in range(im1.shape[0]) for x in range(im1.shape[1])], np.uint32)
  triNums = Delaunay.find_simplex(tri, grid_points[:len(grid_points)-1]) # minor bug: this is causing one point to not be mapped to a triangle
  
  for i in range(len(tri.simplices)):
    tri_dict[i] = grid_points[np.where(triNums == i)]

  return tri_dict

def getValidColorSamplePts(img, xPts, yPts):
  """
  The img will be accessed at locations [yPts, xPts]
  Thus we must ensure that we're not indexing past the boundaries of our image
  This function will cut the largest coordinate location if necesasry to ensure proper indexing
  """
  num_rows, num_columns = img.shape[:2]
  if max(xPts) >= num_columns:
    xPts = xPts[np.where(xPts != max(xPts))[0]]
  if  max(yPts) >= num_rows:
    yPts = yPts[np.where(yPts != max(yPts))[0]]

  # trim pts to the min number since these are coordinates thus len(xPts) must equal len (yPts)

  min_length = min(len(xPts), len(yPts))
  xPts = xPts[:min_length]
  yPts = yPts[:min_length]

  assert(len(xPts) == len(yPts))
  return xPts, yPts

def getWarpedImg(img, tri_dict, inv_transformation, t):
  """
  Given the image and its target triangulation, warp the image towards its target using inv_transformation
  """
  morphed_im = np.zeros((img.shape), dtype=np.uint8)

  # iterate over each triangle
  for i in range(len(tri_dict)):
    tri_pts = np.vstack((tri_dict[i].T, np.ones(len(tri_dict[i])))).T
    warped_pts = np.dot(inv_transformation[i], tri_pts.T).T

    # convert pts to integers since we can't warp fractions of a pixel
    warped_pts = warped_pts.astype(int)
    warped_y_pts = warped_pts.T[1]
    warped_x_pts = warped_pts.T[0]

    if (len(warped_x_pts) == 0 or len(warped_y_pts) == 0):
      print('no warped pts available')
      continue
   
    try:
      warped_x_pts, warped_y_pts = getValidColorSamplePts(img, warped_x_pts, warped_y_pts)
      warped_colors = img[warped_y_pts, warped_x_pts]
    except:
      print(i, len(tri_dict), warped_x_pts.shape, warped_y_pts.shape)
      raise

    try:
      # pdb.set_trace()
      img_pts = tri_dict[i]
      img_x_pts, img_y_pts = img_pts.T[0], img_pts.T[1]
      morphed_im[img_y_pts, img_x_pts] = warped_colors
    except:
      print(i, morphed_im.shape, len(morphed_im), warped_colors.shape, len(warped_colors), len(warped_x_pts), len(warped_y_pts))
      raise

  return morphed_im

def getInverseTransformation(src_pts, triangulations):
  # Add 1 to each coordinate pair for affine transformation
  src_pts = np.vstack((src_pts.T, np.ones(src_pts.T.shape[1])))

  T_inv_transforms = []
  for i, tri in enumerate(triangulations.simplices):
    tri_pts = triangulations.points[tri]
    src_pts_to_tri = src_pts.T[tri]
    tri_pts = np.vstack((tri_pts.T, np.ones(tri_pts.T.shape[1]))).T
    #https://stackoverflow.com/questions/10326015/singular-matrix-issue-with-numpy
    #A = np.dot(tri_pts.T, np.linalg.inv(src_pts_to_tri.T))
    #A_inv = np.linalg.inv(A)

    try:
      A = np.dot(tri_pts.T, np.linalg.pinv(src_pts_to_tri.T))
      A_inv = np.linalg.pinv(A)
    except:
      logging.info("Singular matrix detected..")
      raise
    T_inv_transforms.append(A_inv)
  return T_inv_transforms

def getMorphSequence(img1_name, img2_name, t_step=0.2):
  """
  t_step is the time step between each iteration of the morph (0 to 1)
  """
  t = 0.0
  while (t <= 1):
    morph(img1_name, img2_name, t)
    t += t_step
  return "Morph sequence is complete"

def saveImg(morphedImg):
  fileHash = uuid.uuid4()
  img_filename = fileHash.hex + '.jpg'
  morphed_img_path = 'morph/content/temp_morphed_images/' + img_filename    # location of saved image
  morphed_img_uri = 'https://sammyjaved.com/facemorphs/' + img_filename     # /facemorphs directory serves static content via nginx
  imageio.imwrite(morphed_img_path, morphedImg)
  logging.info(img_filename)

  return morphed_img_uri

def morph(img1, img2, t):
  """'
  Create morph from img1 to img2 at time t
  """
  img1_corresponding_pts = getDetectedCorrespondingPoints(img1)
  img2_corresponding_pts = getDetectedCorrespondingPoints(img2)

  midPoints = crossDisolve(img1_corresponding_pts, img2_corresponding_pts, t, isImage=False)   # avg of the img point sets
  midpoint_tesselation = Delaunay(midPoints)

  img1_tri_to_point = getTriPoints(img1, midpoint_tesselation)
  img2_tri_to_point = getTriPoints(img2, midpoint_tesselation)

  T1_inv_dict = getInverseTransformation(img1_corresponding_pts, midpoint_tesselation)
  T2_inv_dict = getInverseTransformation(img2_corresponding_pts, midpoint_tesselation)

  img1_warped = getWarpedImg(img1, img1_tri_to_point, T1_inv_dict, t)
  img2_warped = getWarpedImg(img2, img2_tri_to_point, T2_inv_dict, t)

  ## for testing purposes only
  saveImg(img1_warped)
  saveImg(img2_warped)
  ##

  morphed_im = crossDisolve(img1_warped, img2_warped, t)
  morphed_img_uri = saveImg(morphed_im)
  
  return morphed_img_uri

###########################################################################################
# TEMPORARY FOR TESTING"
###########################################################################################

small_im1_filename = 'morph/content/images/obama_small.jpg'
small_im2_filename = 'morph/content/images/george_small.jpg'

big_im1_filename = 'morph/content/images/obama_fit.jpg'
big_im2_filename = 'morph/content/images/clooney_fit.jpg'

big_im1_filename = 'morph/content/images/tiger_high.jpg'
big_im2_filename = 'morph/content/images/adele_high.jpg'

# Load small images for regression testing
img1_filename = small_im1_filename
img2_filename = small_im2_filename

# Load larger images for performance testing
# img1_filename = big_im1_filename
# img2_filename = big_im2_filename

img1 = sk.io.imread(img1_filename)
img2 = sk.io.imread(img2_filename)
log_message = 'Morphing ', (img1_filename, img2_filename)
logging.info(log_message)
morphed_img_uri = morph(img1, img2, 0.5)
