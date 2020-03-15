# https://blog.realkinetic.com/building-minimal-docker-containers-for-python-applications-37d0272c52f3
# Elegantly activating a virtualenv in a Dockerfile https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
# Python 2.7 + dlib: https://hub.docker.com/r/cameronmaske/dlib/dockerfile
# django and nginx for production https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html
# gunicorn https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/

# BUILD IMAGE: [use SCREEN FIRST!]: docker build -t face-morpher-api:stage -f Dockerfile .
# RUN CONTAINER: docker run -p 8088:8088 --rm face-morpher-api:stage 
# SHELL: docker container run -it -p 8088:8088 -v /home/sammy/ImageMorpher:/app face-morpher-api:stage bash

FROM ubuntu:18.04
RUN apt-get update
RUN apt-get upgrade -y python3
RUN apt-get install -y python3-pip python3-dev build-essential vim
RUN pip3 install --upgrade virtualenv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m virtualenv --python=/usr/bin/python3 $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

COPY requirements.txt .

# this command was primarily copied for cmake
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
    libjpeg-dev \
    liblapack-dev \
    libswscale-dev \
    # libsystemd-journal-dev \
    # libsystemd-daemon-dev \
    # libsystemd-dev \
    pkg-config \
    python-dev \
    python-numpy \
    python-protobuf\
    software-properties-common \
    zip \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install -r requirements.txt --verbose

ENV PORT_NUM=8088

# CMD ["python", "manage.py", "runserver", PORT_NUM]
# CMD python manage.py runserver 0:8088
# python manage.py runserver 0:8088 # development server
