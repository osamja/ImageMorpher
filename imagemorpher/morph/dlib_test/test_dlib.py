import skimage.io as skio
import numpy as np
import dlib

img1_name = 'adele_small.jpg'
img2_name = 'lady.jpg'

img1 = skio.imread(img1_name)
img2 = skio.imread(img2_name)
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
img1_face = detector(img1, 1)[0]      # get first face
img2_face = detector(img2, 1)[0]      # get first face
img1_face_detection_object = predictor(img1, img1_face)
img2_face_detection_object = predictor(img2, img2_face)
img1_face_points = img1_face_detection_object.parts()
img2_face_points = img2_face_detection_object.parts()
