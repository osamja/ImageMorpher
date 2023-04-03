########################################################################

# BUILD CONTAINER: docker build --memory=2g --memory-swap=4g --cpuset-cpus=1 -t face-morpher-api:dev -f dev.Dockerfile .
# RUN CONTAINER: docker run -it -p 8088:8088 -v /home/sammy/ImageMorpher:/app --rm face-morpher-api:dev bash
# START SERVER: python manage.py runserver 0:8088

# PURPOSE:
# The purpose of this dockerfile was an attempt at simplying the Dockerfile
# dependencies. Tried to install less packages, not use dlib, avoid virtual env
# with a conda base image.  But running into too many issues.  I think any 
# refactor should maybe not be a clean start but a slow refactor on Dockerfile

########################################################################

# Use anaconda as a base image
FROM continuumio/anaconda3

# Update package manager
RUN apt-get update
RUN apt-get upgrade -y python3

# Install python3 and pip3
RUN apt-get install -y python3-pip python3-dev vim

# Install virtualenv
# RUN pip3 install --upgrade virtualenv
# ENV VIRTUAL_ENV=/opt/venv
# RUN python3 -m virtualenv --python=/usr/bin/python3 $VIRTUAL_ENV
# ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# install cmake
RUN apt-get install -y cmake

RUN pip3 install django dlib djangorestframework gunicorn autocrop django-cors-headers 

RUN pip3 install scikit-image

# Set working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install requirements
RUN pip install -r requirements.txt

# Expose port 8088
EXPOSE 8088
