# ImageMorpher
* This application exposes a public API for morphing two faces together
* Built on top of the Django web framework
* The ImageMorpher container is managed via docker-compose in the nginx proxy
* Uses gunicorn as its WSGI

<!-- # https://blog.realkinetic.com/building-minimal-docker-containers-for-python-applications-37d0272c52f3
# Elegantly activating a virtualenv in a Dockerfile https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
# Python 2.7 + dlib: https://hub.docker.com/r/cameronmaske/dlib/dockerfile
# django and nginx for production https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html
# gunicorn https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/ -->

## Redis
- Start a Redis container by running the following command in a named SCREEN session:
`docker run --name my-redis -it redis`

# DEVELOPMENT:
- Start or resume a screen session: `screen -S <session-name>` or `screen -r <session-name>`
- Build docker image
    - `docker build --memory=2g --memory-swap=4g --cpuset-cpus=1 -t face-morpher-api:dev -f Dockerfile .`
- Start dev server container linked to redis
    - `docker container run --rm -it --link my-redis:redis -p 8088:8088 -v /home/sammy/ImageMorpher:/app face-morpher-api:dev bash`
- Run django development server
    - `python manage.py runserver 0:8088`
- Run django dramatiq worker in a separate container but linked to redis
    - `docker container run -it --link my-redis:redis -v /home/sammy/ImageMorpher:/app face-morpher-api:dev bash`
    - `python manage.py rundramatiq`

Server: [use SCREEN FIRST!]: docker build -t face-morpher-api -f Dockerfile .
docker build --memory=2g --memory-swap=4g --cpuset-cpus=1 -t face-morpher-api -f Dockerfile .
Local Mac: docker build -t face-morpher-api -f Dockerfile .

# SHELL INTO CONTAINER:
   - `docker container run --rm -it -p 8088:8088 -v /home/sammy/ImageMorpher:/app face-morpher-api bash`

# To update production with latest code changes
#   SSH into server, enter screen session running docker-compose
#       screen -ls              # view existing screen sessions
#       screen -r <session-id>  # attach to existing screen
#       Control + a + d         # Run screen as background process
#   docker-compose down; docker-compose up
#   Since the morph container references the volume, as long as the files are updated on the server; that will be served to the user


### Run a command in the dev ImageMorpher docker container linked to Redis
docker container run -it -v /home/sammy/ImageMorpher:/app dev-face-morpher-api bash

# some notes for tasks queued with dramatiq
docker container run -it --link my-redis:redis -p 8088:8088 -v /home/sammy/ImageMorpher:/app face-morpher-api bash
docker container run -it --link my-redis:redis -v /home/sammy/ImageMorpher:/app face-morpher-api bash
docker exec -it c60253c52a40 redis-cli ping


## Unit Test
* Shell into Image morpher docker container
* Run `./manage.py test`

- Interact with the Redis container using the redis-cli command. To connect to the Redis server running inside the container, run the following command:
`docker exec -it my-redis-container redis-cli`

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


<!-- from dockerfile -->
# https://blog.realkinetic.com/building-minimal-docker-containers-for-python-applications-37d0272c52f3
# Elegantly activating a virtualenv in a Dockerfile https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
# Python 2.7 + dlib: https://hub.docker.com/r/cameronmaske/dlib/dockerfile
# django and nginx for production https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html
# gunicorn https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/

# BUILD IMAGE: 
#   Server: [use SCREEN FIRST!]: docker build -t face-morpher-api -f Dockerfile .
#   docker build --memory=2g --memory-swap=4g --cpuset-cpus=1 -t face-morpher-api -f Dockerfile .
#   Local Mac: docker build -t face-morpher-api -f Dockerfile .

# SHELL INTO CONTAINER:
#   Server: docker container run -it -p 8088:8088 -v /home/sammy/ImageMorpher:/app face-morpher-api bash

# Local Mac: docker container run -it -p 8088:8088 -v /Users/sjaved/projects/personal/ImageMorpher:/app face-morpher-api bash

# Dev Server: 
#   docker container run -it -p 8088:8088 -v /home/sammy/ImageMorpher:/app face-morpher-api bash
#   cd imagemorpher;
#   python manage.py runserver 0:8088
# Then use Postman collection to call endpoints

# To update production with latest code changes
#   SSH into server, enter screen session running docker-compose
#       screen -ls              # view existing screen sessions
#       screen -r <session-id>  # attach to existing screen
#       Control + a + d         # Run screen as background process
#   docker-compose down; docker-compose up
#   Since the morph container references the volume, as long as the files are updated on the server; that will be served to the user

