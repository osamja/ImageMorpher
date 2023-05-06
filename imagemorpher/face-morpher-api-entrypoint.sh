#!/bin/bash

# entrypoint for the face morpher api docker container

# Run Django migrations
python manage.py makemigrations
python manage.py migrate

# Start the application
exec "$@"
