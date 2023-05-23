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
    libpq-dev \
    libswscale-dev \
    pkg-config \
    postgresql-client \
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

# This is where we add the fix for the algorithm issue, this is needed
# before we pip install pyjwt[crypto]
RUN pip uninstall -y pyOpenSSL
RUN pip install pyOpenSSL

RUN pip install 'dramatiq[redis, watch]' django_dramatiq psycopg2-binary pyjwt[crypto]

ENV PORT_NUM=8088
