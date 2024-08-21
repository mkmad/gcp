#!/bin/bash

# Install Python3 pip
echo "Starting installation of python3-pip..."
if apt install -y python3-pip; then
    echo "python3-pip installed successfully."
else
    echo "Failed to install python3-pip." >&2
    exit 1
fi

# Install Python dependencies from requirements.txt
echo "Installing Python dependencies from requirements.txt..."
if pip install -r requirements.txt; then
    echo "Dependencies installed successfully."
else
    echo "Failed to install dependencies." >&2
    exit 1
fi

# Install Docker
echo "Downloading and installing Docker..."
if curl -fsSL https://get.docker.com -o get-docker.sh; then
    echo "Docker script downloaded successfully."
else
    echo "Failed to download Docker script." >&2
    exit 1
fi

if sudo sh get-docker.sh; then
    echo "Docker installed successfully."
else
    echo "Failed to install Docker." >&2
    exit 1
fi

# Enable Docker service
echo "Enabling Docker service..."
if sudo systemctl enable docker; then
    echo "Docker service enabled successfully."
else
    echo "Failed to enable Docker service." >&2
    exit 1
fi

# Install Google Cloud Transfer Agent
echo "Installing Google Cloud Transfer Agent..."
if /snap/google-cloud-cli/260/lib/gcloud.py transfer agents install --pool=sts --id-prefix=sts --mount-directories=/; then
    echo "Google Cloud Transfer Agent installed successfully."
else
    echo "Failed to install Google Cloud Transfer Agent." >&2
    exit 1
fi

# Start the Gunicorn server
echo "Starting Gunicorn server..."
if gunicorn -w 4 -b 0.0.0.0:5001 process:app --daemon; then
    echo "Gunicorn server started successfully."
else
    echo "Failed to start Gunicorn server." >&2
    exit 1
fi
