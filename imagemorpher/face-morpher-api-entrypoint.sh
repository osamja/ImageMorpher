#!/bin/bash

# Check if we want to enable debugging
if [ "$MORPH_DEBUG" = "true" ]; then
    echo "Debugging enabled: Waiting for debugger to attach on port $DEBUG_PORT..."
    # Start debugpy on the specified port (default to 5678 if not set)
    # install debug py
    pip install debugpy
    python -m debugpy --listen 0.0.0.0:$DEBUG_PORT --wait-for-client manage.py runserver 0.0.0.0:8000
else
    # Run the usual Django server without debugging
    python manage.py runserver 0.0.0.0:8000
fi