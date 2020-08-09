import matplotlib.pyplot as plt
from skimage import img_as_ubyte
import skimage.io as skio
from PIL import Image
from autocrop import Cropper
import imageio
import pdb
import os
from django.utils.text import get_valid_filename
import cv2

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

def isImageTypeSupported(img_path):
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

def getFormattedImages(img1_path, img2_path):
    """
    Return img1, img2 cropped and with similar dimensions for optimal results
    img1 may be a filepath string or a InMemoryUploadedFile
    """
    # Note: WE CAN ONLY READ THE FILE ONCE!

    if (not (isImageTypeSupported(img1_path) and isImageTypeSupported(img2_path))):
        raise ValueError('Image file type is not supported: ')

    pil_img1 = Image.open(img1_path)
    pil_img2 = Image.open(img2_path)

    cropper = Cropper()

    img1 = getImageReadyForCrop(pil_img1)
    img2 = getImageReadyForCrop(pil_img2)

    img1_cropped = cropper.crop(img1)
    img2_cropped = cropper.crop(img2)

    img1_cropped_cv = cv2.cvtColor(img1_cropped, cv2.COLOR_BGR2RGB)
    img2_cropped_cv = cv2.cvtColor(img2_cropped, cv2.COLOR_BGR2RGB)

    # For debugging purposes only, compare uncropped vs cropped image for color inspection
    # imageio.imwrite('img1.jpg', img1)
    # imageio.imwrite('img2.jpg', img2)
    # imageio.imwrite('img1_cropped.jpg', img1_cropped_cv)
    # imageio.imwrite('img2_cropped.jpg', img2_cropped_cv)
    return img1_cropped_cv, img2_cropped_cv
