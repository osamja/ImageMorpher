# Summer 2019:
Going to try to refactor this code, then maybe try to port it to the web

### Plan
* Draw three pts for a triangle
* Fill in the triangle with a solid color
* Create a new triangle that is a 45 deg rotation (use affine rotation transformation) of the existing triangle
* Find the midway pt between a target and destination triangle pt, paint it
* Find interpolated points at time t between target and dest pts, this will be our A' matrix that we are transforming to.  Find the transform T' that gets us here
* Apply T' to all pixels in target triangle to find the transformed warped triangle
* Keep doing this for steps in t
* How does inverse warping work?

### Backlog
- Cast from floating point to 2 decimal places for faster compute

### Selecting Corresponding Points
Left eyebrow
 * left
 * middle 
 * right 
* Between eyebrow 
Right eyebrow
 * left
 * middle 
 * right 
Left Eye
 * left
 * middle 
 * right 
* Between eyes
Right Eye
 * left
 * middle 
 * right 
Left cheek at tip of nose
 * left
 * middle 
 * right 
Nose
 * Left nostril
 * Tip of nose
 * Right nostril
Right cheek at tip of nose
 * left
 * middle 
 * right 
Mouth
 * left
 * middle
 * right
 * Top 
 * Bottom
Jaw
 * Left jaw
 * Right jaw


## Product Vision
* MVP
  - Upload two pictures in web browser, same resolution
  - Manually pick corresponding points on the UI
  - Return the 'midway' image to the user

## Product development journal
Awesome to see getting the refactored morph working
Setup basic Django backend REST endpoint /morph
Build the frontend with React to allow for image uploads
Find out how to read the images in by Python/Django
Find out how to get auto-generated facial landmark corresponding points using dlib library
Find out how to use pixel cropping to detect and delete black parts of the image (morph is smaller than image base layer)
