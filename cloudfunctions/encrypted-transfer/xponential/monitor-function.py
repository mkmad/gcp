import requests
from google.cloud import tasks_v2
import time
import json
from google.protobuf import timestamp_pb2

# Cloud Tasks client
client = tasks_v2.CloudTasksClient()
PROJECT_ID = 'backup-428118'
LOCATION = 'us-west2'
QUEUE_ID = 'monitoring-stats-queue'
PARENT = client.queue_path(PROJECT_ID, LOCATION, QUEUE_ID)

FLASK_APP_URL = "http://35.231.110.68:5001"
MONITORING_APP_URL = "https://us-west2-backup-428118.cloudfunctions.net/monitor"
STAGES = ["download", "compression", "encryption", "drive_upload"]


def check_progress(request):
    """Cloud Function triggered by Cloud Tasks to monitor the stages of a folder."""
    request_json = request.get_json()
    folder_name = request_json.get("folder_name")
    
    all_stages_complete = True  # Assume all stages are complete until proven otherwise
    progress_output = []  # List to accumulate progress output for single line print

    for stage in STAGES:
        progress = fetch_status(stage)
        
        if progress is None:
            return f"Error fetching status for {stage}", 500
        
        # Append the progress of each stage to the output list
        progress_output.append(f"{stage}: {progress}%")
        
        if progress < 100:
            all_stages_complete = False  # If any stage is not complete, continue polling
    
    # Print all stages and their progress in a single line
    print(" | ".join(progress_output))
    
    if all_stages_complete:
        # If all stages are complete, task terminates here
        print(f"All stages for folder {folder_name} are complete. No further tasks will be enqueued.")
        return f"Processing complete for {folder_name}", 200
    else:
        # If not all stages are complete, re-enqueue task for further polling
        enqueue_monitoring_task(folder_name, delay_seconds=60)
        return f"Re-enqueued monitoring task for {folder_name}", 202


def fetch_status(stage):
    """Fetch the status of a given stage from the Flask app."""
    url = f"{FLASK_APP_URL}/status/{stage}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get(stage, 0)  # Return progress percentage
        else:
            print(f"Failed to fetch status for {stage}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching status for stage {stage}: {e}")
        return None


def enqueue_monitoring_task(folder_name, delay_seconds=60):
    """Enqueue a task for monitoring all stages of the folder processing."""
    payload = {"folder_name": folder_name}  # Include all stages
    
    task = {
        'http_request': {  
            'http_method': tasks_v2.HttpMethod.POST,
            'url': f"{MONITORING_APP_URL}/check_progress",  # Your monitoring Cloud Function
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(payload).encode()
        },
        'schedule_time': timestamp_pb2.Timestamp(seconds=int(time.time() + delay_seconds))  # Set delay before task execution
    }
    
    # Create the task in Cloud Tasks
    response = client.create_task(request={"parent": PARENT, "task": task})
    task_name = response.name  # Get the task name (includes task ID)
    
    return task_name
