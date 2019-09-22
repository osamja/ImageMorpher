#!/bin/bash

# This script launches a dockerrized nginx container serving morphed images at the document root

# Run a container mounted to a volume docker 
docker container run -d -v $(pwd)/imagemorpher/morph/temp_morphed_images:/usr/share/nginx/html -p 8080:80 --name nginx-static-content nginx-static-content

