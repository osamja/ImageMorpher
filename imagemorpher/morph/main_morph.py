import skimage as sk
import numpy as np
from .graphics import plotTri, plotImg, plotCorrespondingPoints, plotDelauneyTesselation
import matplotlib.pyplot as plt
from .image_sources import getImages, getCorrespondingPts, addCornerPoints
from scipy.spatial import Delaunay
import time
import imageio
import dlib
import pdb
import datetime

"""
Image Morphing
We know how to warp one image into the other, but
how do we create a morphing sequence?-
1. Create an intermediate shape (by interpolation)
2. Warp both images towards it
3. Cross-dissolve the colors in the newly warped images
"""

def stopWatch(value, message="useless"):
    print(message + " took seconds: ", int(value))

def getDetectedCorrespondingPoints(img):
  detector = dlib.get_frontal_face_detector()
  predictor = dlib.shape_predictor('/home/sammy/development/ImageMorpher/imagemorpher/morph/shape_predictor_68_face_landmarks.dat')
  face = detector(img, 1)[0]      # get first face
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
  first_image = (1-t) * pts1
  second_image = (t) * pts2
  if (isImage):
    dissolveImg = np.add(first_image.astype(np.uint8), second_image.astype(np.uint8))
  else:
    dissolveImg = np.add(first_image, second_image)
  return dissolveImg

def getTriPoints(im1, tri):
  tri_dict = {}
  tri_dict[-1] = []
  for iter, t in enumerate(tri.simplices):
    tri_dict[iter] = []

  # Sort every pixel into our triangles
  for row in range(im1.shape[0]):
    for column in range(im1.shape[1]):
      pt = np.array([column, row])
      triNum = int(Delaunay.find_simplex(tri, pt))
      # triNum = int(tsearch(tri, pt))
      tri_dict[triNum].append(pt)
  return tri_dict

# Given a 2D point, returns the homogenous point coordinate.
def getHomoPt(pt):
  pt = pt.reshape(2, 1)
  return np.pad(pt, ((0, 1), (0, 0)), mode='constant', constant_values=1)

def shouldClipPixel(img_shape, px, py):
  w, h = img_shape[1]-1, img_shape[0] - 1
  if (px > w or py > h):
    return True
  return False

# Clip values outside the boundaries of our image
def clipValues(im1, im2, px, py, px2, py2):
  w, h = im1.shape[1] - 1, im1.shape[0] - 1
  if (px > w):
    px = w
  if (px2 > w):
    px2 = w
  if (py > h):
    py = h
  if (py2 > h):
    py2 = h
  return px, py, px2, py2

# For every pixel that wasn't in a triangle, fill it in.
def fillNonTrianglePixels(im1, im2, new_im, tri_dict, alpha):
	for p in tri_dict[-1]:
		x = p[0]
		y = p[1]
		color1 = im1[y][x]
		color2 = im2[y][x]
		new_im[y][x] = (1-alpha) * color1 + alpha * color2
	return new_im

def getMorphedImg(src_img, dest_img, tri, tri_dict, T1_inv, T2_inv, t):
  morphed_im = np.zeros(src_img.shape, dtype=np.uint8)
  morph_amount = t
  source_image = src_img
  destination_image = dest_img

  for i, triangle in enumerate(tri.simplices):
    for p in tri_dict[i]:
      b = getHomoPt(p)
      x = np.dot(T1_inv[i], b)
      x2 = np.dot(T2_inv[i], b)
      pixel_x = int(np.around(x[0]))  # round rather than interpolate for now
      pixel_y = int(np.around(x[1]))
      pixel_x2 = int(np.around(x2[0]))
      pixel_y2 = int(np.around(x2[1]))

      #may not be needed
      if (shouldClipPixel(src_img.shape, pixel_x, pixel_y) or shouldClipPixel(dest_img.shape, pixel_x2, pixel_y2)):
        continue

      color1 = src_img[pixel_y][pixel_x]
      color2 = dest_img[pixel_y2][pixel_x2]
      morphed_im[p[1]][p[0]] = crossDisolve(color1, color2, t)
    
  return morphed_im

def getInverseTransformationDictionary(src_pts, triangulations):
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
      print("Singular matrix at index ", i)
      raise
    T_inv_transforms.append(A_inv)
  return T_inv_transforms

def getMorphSequence(img1_name, img2_name, t_step):
  """
  t_step is the time step between each iteration of the morph (0 to 1)
  """
  t = 0.0
  while (t <= 1):
    morph(img1_name, img2_name, t)
    t += t_step
  return "Morph sequence is complete"

def crop_image_blacked_rows(img,tol=0):
  mask = img>tol
  if img.ndim==3:
      mask = mask.all(2)
  mask0,mask1 = mask.any(0),mask.any(1)
  return img[np.ix_(mask0,mask1)]

def morph(img1, img2, t):
  """'
  Create morph from img1 to img2 at time t
  """
  img1_corresponding_pts = getDetectedCorrespondingPoints(img1)
  img2_corresponding_pts = getDetectedCorrespondingPoints(img2)
  midPoints = crossDisolve(img1_corresponding_pts, img2_corresponding_pts, t, isImage=False)   # avg of the img point sets
  midpoint_tesselation = Delaunay(midPoints)
  tri_to_point_dict = getTriPoints(img1, midpoint_tesselation)
  img1_affine_pts = np.vstack((img1_corresponding_pts.T, np.ones(img1_corresponding_pts.T.shape[1])))# Add 1 to each coordinate pair for affine transformation
  img2_affine_pts = np.vstack((img2_corresponding_pts.T, np.ones(img2_corresponding_pts.T.shape[1])))
  T1_inv_dict = getInverseTransformationDictionary(img1_affine_pts, midpoint_tesselation)
  T2_inv_dict = getInverseTransformationDictionary(img2_affine_pts, midpoint_tesselation)
  morphed_im = getMorphedImg(img1, img2, midpoint_tesselation, tri_to_point_dict, T1_inv_dict, T2_inv_dict, t)
  morphed_img_path = 'morph/temp_morphed_images/' + str(datetime.datetime.now()) + '.jpg'
  imageio.imwrite(morphed_img_path, morphed_im)
  return morphed_img_path
