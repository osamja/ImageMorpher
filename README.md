# ImageMorpher
* This application exposes a public API for morphing two faces together
* Built on top of the Django web framework
* The ImageMorpher container is managed via docker-compose in the nginx proxy
* Uses gunicorn as its WSGI

### Start Django development server
* Shell into Image morpher docker container
* `python manage.py runserver 0:8000`

## Unit Test
* Shell into Image morpher docker container
* Run `./manage.py test`

### 

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

# Privacy
* To delete all images for a certain month we can use the following command.  Note: This deletes all filenames that begin with 2021-11, aka files that were created in november of 2021. 
`cd /home/sammy/ImageMorpher/imagemorpher/morph/content/temp_morphed_images`

# delete files for a given month
`find . -type f -name "2021-11*" -delete`

# count number of files
`find . -type f -name "2022-03*" | wc -l`

# cron tab to automatically delete old files
See `auto_delete.py`
