import os
import requests
import time
from google_auth_oauthlib.flow import InstalledAppFlow

import google.auth

# Flask app base URL
BASE_URL = "http://127.0.0.1:5001"

# Folder name to process
folder_name = "takeout-export-f9d7e813-bad7-42f8-b66c-3c0712e1f0de"

# Stages to monitor
stages = ["compression", "encryption", "drive_upload", "download"]

# OAuth 2.0 settings
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/devstorage.read_write',
    'https://www.googleapis.com/auth/cloud-platform'
]
CLIENT_SECRETS_FILE = 'local_secret.json'
ADC_SECRET_FILE = 'rowhouse-creds.json'
AUTH_PORT = 5002

def get_adc_credentials():
    # Set the GOOGLE_APPLICATION_CREDENTIALS environment variable
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ADC_SECRET_FILE

    # Fetch Application Default Credentials
    credentials, project = google.auth.default()
    return credentials

def get_oauth_credentials():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=AUTH_PORT)
    return credentials

def create_folder(folder_name):
    """Send a request to create a folder if it does not exist."""
    url = f"{BASE_URL}/create_folder"
    response = requests.post(url, json={"folder_name": folder_name})
    if response.status_code == 201:
        print(f"Folder {folder_name} created successfully.")
    elif response.status_code == 200:
        print(f"Folder {folder_name} already exists.")
    else:
        print(f"Failed to create folder: {response.text}")
        raise Exception(f"Failed to create folder: {response.text}")

def start_process(folder_name, credentials):
    """Send a request to start processing the folder."""
    url = f"{BASE_URL}/process"
    credentials_dict = {"key": "val"}
    response = requests.post(url, json={"folder_name": folder_name, "credentials": credentials_dict})
    if response.status_code == 202:
        print(f"Processing started for folder: {folder_name}")
        return True
    else:
        print(f"Failed to start processing: {response.text}")
        return False

def fetch_status(stage):
    """Fetch the status of a given stage."""
    url = f"{BASE_URL}/status/{stage}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get(stage, 0)
    else:
        print(f"Failed to fetch status for {stage}: {response.json()}")
        return None

def monitor_progress():
    """Monitor and print the progress of each stage every 5 seconds."""
    start_time = time.time()

    while True:
        all_stages_completed = True
        progress_status = []

        for stage in stages:
            progress = fetch_status(stage)
            if progress is not None:
                progress_status.append(f"{stage.capitalize()}: {progress}%")
            if progress < 100:
                all_stages_completed = False

        print("Progress: " + " | ".join(progress_status), end='\n')

        if all_stages_completed:
            print("\nAll stages completed.")
            break

        time.sleep(60)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Total time taken: {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    credentials = {}
    create_folder(folder_name)
    if start_process(folder_name, credentials):
        monitor_progress()
