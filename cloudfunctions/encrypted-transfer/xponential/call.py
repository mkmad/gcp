import requests
import time

# Flask app base URL
BASE_URL = "http://34.31.222.16:5001"

# Folder name to process
folder_name = "/Users/mohan/Desktop/xponential/5Giga"

# Stages to monitor
stages = ["compression", "encryption", "drive_upload"]

def start_process(folder_name):
    """Send a request to start processing the folder."""
    url = f"{BASE_URL}/process"
    response = requests.post(url, json={"folder_name": folder_name})
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
    if start_process(folder_name):
        monitor_progress()
