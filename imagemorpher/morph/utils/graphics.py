import matplotlib.pyplot as plt
from skimage import img_as_ubyte
import skimage.io as skio
from PIL import Image

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

def getFormattedImage(img):
    img = skio.imread(img)
    img = Image.fromarray(img)
    img = img.convert("RGB")
    img = img_as_ubyte(img)

    return img
