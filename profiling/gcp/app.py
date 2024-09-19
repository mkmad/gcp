from flask import Flask
import googlecloudprofiler
import os
import random

app = Flask(__name__)

# Initialize Google Cloud Profiler
try:
    googlecloudprofiler.start(
        service='my-python-service',  # Replace with your service name
        service_version='1.0.0',      # Replace with your service version
        verbose=3,                    # Log level (0-3)
    )
except (ValueError, NotImplementedError) as exc:
    print(f"Cloud Profiler failed to start: {exc}")

# Memory-intensive task: generate a large list of random numbers
def memory_intensive_task():
    large_list = [random.random() for _ in range(10**7)]  # List with 10 million floats
    return f"Generated a list with {len(large_list)} numbers."

@app.route('/')
def hello_world():
    return memory_intensive_task()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
