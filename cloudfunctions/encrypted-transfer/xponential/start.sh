#!/bin/bash

# # Install Python3 pip
# echo "Starting installation of python3-pip..."
# if apt install -y python3-pip; then
#     echo "python3-pip installed successfully."
# else
#     echo "Failed to install python3-pip." >&2
#     exit 1
# fi

# Install Python dependencies from requirements.txt
echo "Installing Python dependencies from requirements.txt..."
if pip install -r requirements.txt; then
    echo "Dependencies installed successfully."
else
    echo "Failed to install dependencies." >&2
    exit 1
fi

# Start the Gunicorn server
echo "Starting Gunicorn server..."
if gunicorn -w 1 -b 0.0.0.0:5001 process:app; then
    echo "Gunicorn server started successfully."
else
    echo "Failed to start Gunicorn server." >&2
    exit 1
fi