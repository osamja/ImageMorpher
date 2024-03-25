import sys
# morph is essentially the src root directory in this file now
#   aka import all files with morph/<file-path>
sys.path.insert(0, '/app/imagemorpher/morph')

import matplotlib.pyplot as plt
from skimage import img_as_ubyte
import skimage.io as skio
from PIL import Image
from autocrop import Cropper
import imageio
import pdb
import os
from django.utils.text import get_valid_filename
from django.http import HttpResponse
import cv2
import base64
from io import BytesIO
import re
import io
import uuid
import datetime
from morph.utils.date import getMorphDate
import dlib
import numpy as np

from morph.exceptions.CropException import CropException
from morph.exceptions.FaceDetectException import FaceDetectException

import logging
logging.basicConfig(filename='morph/logs/morph-app-perf.log', level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

# Plots the given points into vertices with edges.
# ex. plotTri(tri, tri.points)
def plotTri(tri):
    pts = tri.points
    plt.triplot(pts[:,0], pts[:,1], tri.simplices.copy())
    plt.plot(pts[:,0], pts[:,1], 'o')
    plt.show()

def plotImg(img):
    plt.imshow(img)
    plt.show()

def plotCorrespondingPoints(pts):
    plt.plot(pts[0], pts[1], 'ro')
    plt.show()

def plotCorrespondingPointsOnImg(corresponding_pts, img):
    return

def plotDelauneyTesselation(tri, points):
    plt.triplot(points[:,0], points[:,1], tri.simplices)
    plt.plot(points[:,0], points[:,1], 'o')
    plt.show()

# This function is similar to the one in morph.py
#  except it returns whether the face was detected or not
def isDetectedCorrespondingPoints(img):
  detector = dlib.get_frontal_face_detector()
  predictor = dlib.shape_predictor('morph/utils/shape_predictor_68_face_landmarks.dat')

  try:
    face = detector(img, 1)[0]      # get first face
  except Exception as e:
    # ideally here, we return this in the HTTP Response
    logging.error("Could not find corresponding points..")
    raise FaceDetectException("Could not find corresponding points..")
  face_detection_object = predictor(img, face)
  face_points = face_detection_object.parts()
  landmarks = np.array([[p.x, p.y] for p in face_points])

  if (len(landmarks) == 0):
    raise FaceDetectException("Could not find corresponding points..")
  
  return True

def isImageTypeSupported(img_path):
    if (isBase64Image(img_path)):
        return True

    if (isinstance(img_path, str)):
        filename, file_extension = os.path.splitext(img_path)
    else: # assume in memory uploaded file
        img_name = img_path.name
        filename, file_extension = os.path.splitext(img_name)
    file_extension = file_extension.lower()
    supportedFileTypes = ['.jpg', '.jpeg', '.png']

    if (file_extension in supportedFileTypes):
        return True

    return False

def getImageReadyForCrop(img):
    img = img_as_ubyte(img)

    # In case img is a PNG with a 4th transparency layer, remove this layer
    # This is pretty hacky and may cause bugs; investigate later
    img = img[:, :, :3]

    return img


"""
# simple hack
# on web, file type is InMemoryUploadedFile
# on mobile, a base64 representation of the image is sent
# TODO: Make base64 check more robust
"""
def isBase64Image(img_path):
    if (type(img_path) == str):
        if ('data:image/jpeg;base64' in img_path):
            return True
        
        if ('/9j' in img_path):
            return True

        # if (base64.b64encode(base64.b64decode(img_path)) == img_path):
        #     return True

    return False

def getCroppedImagePath(img):
    """
    Given an image, returns img path where cropped file has been saved
    img may be a filepath string or a InMemoryUploadedFile
    """
    if (not(img)):
        raise CropException('No image provided')

    if (not (isImageTypeSupported(img))):
        raise CropException('File type not supported')

    morphDate = getMorphDate()
    fileHash = uuid.uuid4()
    img_filename = morphDate + '-' + fileHash.hex + '.jpg'
    morphed_img_path = 'morph/content/temp_morphed_images/' + img_filename    # location of saved image

    if (isBase64Image(img)):
        img_stripped_b64 = re.sub('^data:image/.+;base64,', '', img)
        img_decoded = base64.b64decode(img_stripped_b64)

        Image.open(io.BytesIO(img_decoded)).convert('RGB').save(morphed_img_path)
        pil_img = Image.open(morphed_img_path)
    else:
        pil_img = Image.open(img)

    cropper = Cropper()

    img = getImageReadyForCrop(pil_img)

    img_cropped = cropper.crop(img)

    img_cropped_cv = cv2.cvtColor(img_cropped, cv2.COLOR_BGR2RGB)

    # For debugging purposes only, compare uncropped vs cropped image for color inspection
    # imageio.imwrite('img1.jpg', img1)
    # imageio.imwrite('img1_cropped.jpg', img1_cropped_cv)

    # Run the cropped face through the face detector to make sure it's a face
    # If it's not a face, raise an exception
    print('Checking if face is detected..')
    is_face_detected = isDetectedCorrespondingPoints(img_cropped_cv)

    if (not is_face_detected):
        raise FaceDetectException('Could not find corresponding points..')

    imageio.imwrite(morphed_img_path, img_cropped_cv)

    return img_filename

def getCroppedImageFromPath(img_path, get_img_path=False):
    morphed_img_path = 'morph/content/temp_morphed_images/' + img_path    # location of saved image
    img = skio.imread(morphed_img_path)

    if (get_img_path):
        return morphed_img_path

    return img
