import requests
import time
from google_auth_oauthlib.flow import Flow
from google.protobuf import timestamp_pb2
from google.cloud import tasks_v2
from google.cloud.exceptions import GoogleCloudError
from urllib.parse import urlparse, parse_qs, urlencode, quote, unquote
import json

# Flask app base URL
SERVER_BASE_URL = "http://35.231.110.68:5001"
MONITORING_APP_URL = "https://us-west2-backup-428118.cloudfunctions.net/monitor"

# Constants
DESTINATION_BUCKET_NAME = 'rowhousebackup'
DESTINATION_FOLDER='/root/'
CLIENT_SECRETS_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/cloud-platform', 'https://www.googleapis.com/auth/drive']
REDIRECT_URI = 'https://us-west2-backup-428118.cloudfunctions.net/StorageTransferFunction'
DRIVE_FOLDER_ID = '0AEKStjCq23zkUk9PVA'
CHUNK_SIZE = 256 * 1024 * 1024  # 256MB chunks
PUBLIC_KEY_FILE = 'xponential_public.asc'
RECIPIENT_EMAIL = 'technology@xponential.com'
ENCRYPT_FILES = False
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds
SERVICE_ACCOUNT_EMAIL = "backuptransfer@backup-428118.iam.gserviceaccount.com"
PROJECT_ID = "backup-428118"
QUEUE_NAME = "monitoring-stats-queue"
LOCATION = "us-west2"
STAGES = ["download", "compression", "encryption", "drive_upload"]

# Set up a Cloud Tasks client
client = tasks_v2.CloudTasksClient()
PARENT = client.queue_path(PROJECT_ID, LOCATION, QUEUE_NAME)


def start_process(folder_name, credentials, auth_code):
    """Send a request to start processing the folder."""
    url = f"{SERVER_BASE_URL}/process"
    credentials_json = credentials.to_json()
    response = requests.post(url, json={"folder_name": folder_name, "credentials": credentials_json, "auth_code": auth_code, "encryption": ENCRYPT_FILES})
    if response.status_code == 202:
        print(f"Processing started for folder: {folder_name}")
        return True
    else:
        print(f"Failed to start processing: {response.text}")
        return False


def fetch_status(stage):
    """Fetch the status of a given stage."""
    url = f"{SERVER_BASE_URL}/status/{stage}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get(stage, 0)
    else:
        print(f"Failed to fetch status for {stage}: {response.json()}")
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
    print(f"Created monitoring task for folder {folder_name}: {response.name}")
    
    return task_name


def get_authorization_url(state):
    """Generate the authorization URL for the OAuth2 flow with a state parameter."""
    print("Generating authorization URL")
    try:
        flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
        auth_url, _ = flow.authorization_url(prompt='consent', state=quote(state))
        return auth_url
    except Exception as e:
        print(f"Failed to generate authorization URL: {e}")
        raise


def fetch_credentials(auth_code):
    """Fetch credentials using the authorization code."""
    print("Fetching credentials using authorization code")
    try:
        flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
        flow.fetch_token(code=auth_code)
        return flow.credentials
    except Exception as e:
        print(f"Failed to fetch credentials: {e}")
        raise


def create_folder(folder_name):
    """Send a request to create a folder if it does not exist."""
    url = f"{SERVER_BASE_URL}/create_folder"
    response = requests.post(url, json={"folder_name": folder_name})
    if response.status_code == 201:
        print(f"Folder {folder_name} created successfully.")
    elif response.status_code == 200:
        print(f"Folder {folder_name} already exists.")
    else:
        print(f"Failed to create folder: {response.text}")
        raise Exception(f"Failed to create folder: {response.text}")


def background_task(auth_code, folder_name):
    """Run the processing task in the background and enqueue a task to monitor all stages."""
    try:
        # Fetch credentials using the OAuth authorization code
        credentials = fetch_credentials(auth_code)

        # Call the create_folder endpoint to ensure folder exists
        create_folder(folder_name)
        
        # Start the process in the Flask app
        if start_process(folder_name, credentials, auth_code):
            # Enqueue a single task to monitor all stages for the folder
            task_name = enqueue_monitoring_task(folder_name, delay_seconds=60)
            return task_name
    except Exception as e:
        print(f"Background task failed: {e}")
        return None


def construct_log_explorer_url():
    """Construct the Log Explorer URL with filters for Cloud Function logs in the project."""
    query = 'resource.type="cloud_function"'
    
    log_explorer_url = (
        f"https://console.cloud.google.com/logs/query;"
        f"query={quote(query)}"
        f"&timeRange=P1D&project={PROJECT_ID}"
    )
    
    return log_explorer_url


def main(request):
    """Entry point for the Cloud Function."""
    print("Processing incoming request")
    request_json = request.get_json(silent=True)
    request_args = request.args
    auth_code = request_json.get('auth_code') if request_json else None

    folder_name = None
    if request_json and 'folder_name' in request_json:
        folder_name = request_json['folder_name']
    elif request_args and 'folder_name' in request_args:
        folder_name = request_args['folder_name']

    if not auth_code:
        url = urlparse(request.url)
        query_params = parse_qs(url.query)
        auth_code = query_params.get('code', [None])[0]
        state = urlencode({'folder_name': folder_name})

        if not auth_code:
            auth_url = get_authorization_url(state)
            print("Redirecting to authorization URL")
            return auth_url, 200, {'Content-Type': 'text/plain'}

    url = urlparse(request.url)
    query_params = parse_qs(url.query)
    state = query_params.get('state', [None])[0]
    if state:
        folder_name = parse_qs(unquote(state)).get('folder_name', [None])[0]

    if not folder_name:
        print('Error: Folder name not provided after OAuth2 flow')
        return 'Error: Folder name not provided after OAuth2 flow', 400

    print(f'Starting process for folder: {folder_name}. Check the logs for progress updates.')

    # Run the background task asynchronously
    task_names = background_task(auth_code, folder_name)

    if task_names:
        # Construct the Log Explorer URL
        log_explorer_url = construct_log_explorer_url()
        print(f"Redirecting to Log Explorer: {log_explorer_url}")
        return '', 302, {'Location': log_explorer_url}
    else:
        return 'Error starting tasks', 500


if __name__ == "__main__":
    main('test')
