# https://blog.realkinetic.com/building-minimal-docker-containers-for-python-applications-37d0272c52f3
# Elegantly activating a virtualenv in a Dockerfile https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
# Python 2.7 + dlib: https://hub.docker.com/r/cameronmaske/dlib/dockerfile
# django and nginx for production https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html
# gunicorn https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/

# BUILD IMAGE: 
#   Server: [use SCREEN FIRST!]: docker build --memory=2g --memory-swap=4g --cpuset-cpus=1 -t face-morpher-api -f Dockerfile .
#   Local Mac: docker build -t face-morpher-api -f Dockerfile .

# RUN CONTAINER: docker run -p 8088:8088 --rm face-morpher-api

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

FROM ubuntu:18.04
RUN apt-get update
RUN apt-get upgrade -y python3
RUN apt-get install -y python3-pip python3-dev build-essential vim
RUN pip3 install --upgrade virtualenv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m virtualenv --python=/usr/bin/python3 $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

# this command was primarily copied for cmake thats necessary for dlib
RUN apt-get update && apt-get install -y \
    cmake \
    curl \
    gfortran \
    git \
    graphicsmagick \
    libgraphicsmagick1-dev \
    libavcodec-dev \
    libavformat-dev \
    libboost-all-dev \
    libgtk2.0-dev \
    libgl1-mesa-glx \
    libjpeg-dev \
    liblapack-dev \
    libswscale-dev \
    pkg-config \
    python-dev \
    python-numpy \
    python-protobuf\
    software-properties-common \
    zip \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# create imagemorpher directory in /app
RUN mkdir imagemorpher
COPY imagemorpher ./imagemorpher
COPY requirements.txt .

RUN mkdir imagemorpher/morph/content/temp_morphed_images

RUN pip install -r requirements.txt

ENV PORT_NUM=8088
