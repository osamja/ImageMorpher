import logging
import os

import numpy as np
from scipy.spatial import Delaunay

from morph.utils.detection import add_corner_points, ensure_corresponding_points, get_corresponding_points
from morph.utils.image_sources import saveImg

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
  """Detect a face in img and return its 68 landmarks plus four corners."""
  return get_corresponding_points(img)


def addCornerPointsOnImg(im1, pts):
  return add_corner_points(im1, pts)


def resizePts(pts1, pts2, compareLength=False):
  """
  Resize the pts as a np array or length wise

  @TODO: Crop the center of the pts to increase the likelihood of retaining the face
  in the img.  Or downsize both images at the beginning of the morph process
  """
  if (compareLength):
    if (len(pts1) != len(pts2)):
      new_length = min(len(pts1), len(pts2))
      pts1 = pts1[:new_length]
      pts2 = pts2[:new_length]
      assert(len(pts1) == len(pts2))
  elif (pts1.shape != pts2.shape):
    new_shape = (min(pts1.shape[0], pts2.shape[0]), min(pts1.shape[1], pts2.shape[1]), 3)
    pts1 = pts1[:new_shape[0], :new_shape[1]]
    pts2 = pts2[:new_shape[0], :new_shape[1]]
    assert(pts1.shape == pts2.shape)

  return pts1, pts2


# Cross Disolve between two images (set of pts) at time t
#  e.g. Image(halfway t:0.5) = (1 - t) * Image_1 + t * Image_2 wh
def crossDisolve(pts1, pts2, t, isImage=True):

  ### Ensure images are same size, else resize them to be scaling up if necessary
  if (isImage):
    pts1, pts2 = resizePts(pts1, pts2)
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
    xPts = xPts[np.where(xPts < num_columns)[0]]
  if  max(yPts) >= num_rows:
    yPts = yPts[np.where(yPts < num_rows)[0]]

  # trim pts to the min number since these are coordinates thus len(xPts) must equal len (yPts)

  min_length = min(len(xPts), len(yPts))
  xPts = xPts[:min_length]
  yPts = yPts[:min_length]

  assert(len(xPts) == len(yPts))
  return xPts, yPts


def getValidWarpPts(img_pts, warp_pts):
  img_pts, warp_pts = resizePts(img_pts, warp_pts)
  return img_pts, warp_pts


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
      print('no warped pts available for triangle #', i)
      continue

    try:
      warped_x_pts, warped_y_pts = getValidColorSamplePts(img, warped_x_pts, warped_y_pts)
      warped_colors = img[warped_y_pts, warped_x_pts]
    except:
      print(i, len(tri_dict), warped_x_pts.shape, warped_y_pts.shape)
      raise

    try:
      img_pts = tri_dict[i]
      img_x_pts, img_y_pts = img_pts.T[0], img_pts.T[1]
      img_x_pts, img_y_pts = getValidColorSamplePts(morphed_im, img_x_pts, img_y_pts)
      assert(len(img_x_pts) == len(img_y_pts))
      img_x_pts, warped_colors = resizePts(img_x_pts, warped_colors, compareLength=True)
      img_y_pts, warped_colors = resizePts(img_y_pts, warped_colors, compareLength=True)
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


def _triangle_regions(dst_pts, simplices, image_shape, epsilon=1e-9):
  """Yield target pixels and barycentric weights for each triangle.

  For every triangle we only walk its bounding box, then keep pixels whose
  barycentric coordinates are non-negative. This replaces a full-image
  ``Delaunay.find_simplex`` call and avoids building a Python tuple per pixel.
  """
  height, width = image_shape[:2]
  dst_pts = np.asarray(dst_pts, dtype=np.float64)

  for simplex in simplices:
    triangle = dst_pts[simplex]
    x0 = max(0, int(np.floor(triangle[:, 0].min())))
    x1 = min(width - 1, int(np.ceil(triangle[:, 0].max())))
    y0 = max(0, int(np.floor(triangle[:, 1].min())))
    y1 = min(height - 1, int(np.ceil(triangle[:, 1].max())))
    if x1 < x0 or y1 < y0:
      continue

    v0 = triangle[1] - triangle[0]
    v1 = triangle[2] - triangle[0]
    det = v0[0] * v1[1] - v1[0] * v0[1]
    if abs(det) < epsilon:
      # Degenerate triangle: it has no area to sample.
      continue

    ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]
    px = xs - triangle[0, 0]
    py = ys - triangle[0, 1]

    beta = (v1[1] * px - v1[0] * py) / det
    gamma = (-v0[1] * px + v0[0] * py) / det
    alpha = 1.0 - beta - gamma

    mask = (alpha >= -epsilon) & (beta >= -epsilon) & (gamma >= -epsilon)
    if not mask.any():
      continue

    yield simplex, xs[mask], ys[mask], alpha[mask], beta[mask], gamma[mask]


def _sample_nearest(img, x, y):
  height, width = img.shape[:2]
  # Match the legacy truncation behavior, but nudge coordinates that are a
  # floating-point hair below an integer (e.g. 19.999999999) back up. Without
  # this, an identity warp can shift the whole image by one pixel.
  xi = np.clip(np.trunc(x + 1e-9).astype(np.int64), 0, width - 1)
  yi = np.clip(np.trunc(y + 1e-9).astype(np.int64), 0, height - 1)
  return img[yi, xi]


def _sample_bilinear(img, x, y):
  height, width = img.shape[:2]
  x = np.clip(x, 0, width - 1)
  y = np.clip(y, 0, height - 1)

  x0 = np.floor(x).astype(np.int64)
  y0 = np.floor(y).astype(np.int64)
  x1 = np.minimum(x0 + 1, width - 1)
  y1 = np.minimum(y0 + 1, height - 1)
  wx = (x - x0)[:, None]
  wy = (y - y0)[:, None]

  top = img[y0, x0] * (1 - wx) + img[y0, x1] * wx
  bottom = img[y1, x0] * (1 - wx) + img[y1, x1] * wx
  return np.clip(top * (1 - wy) + bottom * wy, 0, 255).astype(np.uint8)


def _sample(img, x, y, sampling):
  if sampling == 'nearest':
    return _sample_nearest(img, x, y)
  if sampling == 'bilinear':
    return _sample_bilinear(img, x, y)
  raise ValueError(f'Unknown sampling mode: {sampling}')


def warp_image(img, src_pts, dst_pts, simplices, sampling='nearest'):
  """Warp ``img`` from ``src_pts`` onto the shape ``dst_pts``."""
  out = np.zeros_like(img)
  src_pts = np.asarray(src_pts, dtype=np.float64)

  for simplex, xs, ys, alpha, beta, gamma in _triangle_regions(dst_pts, simplices, img.shape):
    source = src_pts[simplex]
    sx = alpha * source[0, 0] + beta * source[1, 0] + gamma * source[2, 0]
    sy = alpha * source[0, 1] + beta * source[1, 1] + gamma * source[2, 1]
    out[ys, xs] = _sample(img, sx, sy, sampling)

  return out


def warp_images_to_shape(img1, pts1, img2, pts2, dst_pts, simplices, sampling='nearest'):
  """Warp two images onto the same destination shape.

  The target bounding box and barycentric weights are computed once per
  triangle and reused for both images, which is roughly half the work of
  calling :func:`warp_image` twice.
  """
  out1 = np.zeros_like(img1)
  out2 = np.zeros_like(img2)
  pts1 = np.asarray(pts1, dtype=np.float64)
  pts2 = np.asarray(pts2, dtype=np.float64)

  for simplex, xs, ys, alpha, beta, gamma in _triangle_regions(dst_pts, simplices, img1.shape):
    for out, img, points in ((out1, img1, pts1), (out2, img2, pts2)):
      source = points[simplex]
      sx = alpha * source[0, 0] + beta * source[1, 0] + gamma * source[2, 0]
      sy = alpha * source[0, 1] + beta * source[1, 1] + gamma * source[2, 1]
      out[ys, xs] = _sample(img, sx, sy, sampling)

  return out1, out2


def _warp_impl():
  return os.environ.get('MORPH_WARP_IMPL', 'vectorized').lower()


def morph_frame(img1, img2, t, landmarks1=None, landmarks2=None, warp_impl=None, sampling='nearest'):
  """Create a single morphed frame without touching disk.

  ``landmarks1``/``landmarks2`` may be 68-point detections or 72-point
  corresponding points (with corners). Passing them in lets a sequence detect
  faces once instead of once per frame.
  """
  img1_corresponding_pts = ensure_corresponding_points(img1, landmarks1)
  img2_corresponding_pts = ensure_corresponding_points(img2, landmarks2)

  midPoints = crossDisolve(img1_corresponding_pts, img2_corresponding_pts, t, isImage=False)   # avg of the img point sets
  midpoint_tesselation = Delaunay(midPoints)

  implementation = (warp_impl or _warp_impl()).lower()
  if implementation == 'legacy':
    img1_tri_to_point = getTriPoints(img1, midpoint_tesselation)
    img2_tri_to_point = getTriPoints(img2, midpoint_tesselation)

    T1_inv_dict = getInverseTransformation(img1_corresponding_pts, midpoint_tesselation)
    T2_inv_dict = getInverseTransformation(img2_corresponding_pts, midpoint_tesselation)

    img1_warped = getWarpedImg(img1, img1_tri_to_point, T1_inv_dict, t)
    img2_warped = getWarpedImg(img2, img2_tri_to_point, T2_inv_dict, t)
  elif implementation == 'vectorized':
    img1_warped, img2_warped = warp_images_to_shape(
      img1,
      img1_corresponding_pts,
      img2,
      img2_corresponding_pts,
      midPoints,
      midpoint_tesselation.simplices,
      sampling=sampling,
    )
  else:
    raise ValueError(f'Unknown MORPH_WARP_IMPL: {implementation}')

  return crossDisolve(img1_warped, img2_warped, t)


def getMorphSequence(img1_name, img2_name, t_step=0.2):
  """
  t_step is the time step between each iteration of the morph (0 to 1)
  """
  t = 0.0
  while (t <= 1):
    morph(img1_name, img2_name, t)
    t += t_step
  return "Morph sequence is complete"


def morph(img1, img2, t, filepath=None, landmarks1=None, landmarks2=None, warp_impl=None, sampling='nearest'):
  """
  Create morph from img1 to img2 at time t
  """
  morphed_im = morph_frame(
    img1,
    img2,
    t,
    landmarks1=landmarks1,
    landmarks2=landmarks2,
    warp_impl=warp_impl,
    sampling=sampling,
  )
  morphed_img_filename = saveImg(morphed_im, filepath)

  return morphed_img_filename, morphed_im
