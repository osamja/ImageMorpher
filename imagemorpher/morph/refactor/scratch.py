
"""
ARCHIVE

halfwayImg = crossDisolve(img1, img2, .5)
plt.imshow(halfwayImg)


plt.show()

# Create a red square image array using Numpy
redSquare = np.full((5,5,3), [255, 0, 0], dtype=np.uint8)
blueSquare = np.full((5,5,3), [0, 0, 255], dtype=np.uint8)
lady = skio.imread('images/lady.jpg')
tiger = skio.imread('images/tiger.jpg')
square_x_pts = [0, 1, 1, 0]
square_y_pts = [0, 0, 1, 1]
square_ones = np.ones(4)
square = np.vstack((square_x_pts, square_y_pts)) # 2x4
square = np.vstack((square, square_ones)) # 3x4

img1 = redSquare
img2 = blueSquare
halfwayImg = crossDisolve(img1, img2, .5)
plt.imshow(halfwayImg)
plt.show()
# Return the transformation T that transforms pts to pts_
# pts_ = pts * T
def warp(pts, pts_):
  return

def affineTransform(pts, transform):
  return ''
  """