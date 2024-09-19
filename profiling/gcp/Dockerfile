# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV GAE_PROFILER_ENABLED true

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip  # Ensure pip is up to date
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Set the working directory to /app
WORKDIR /app

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]
