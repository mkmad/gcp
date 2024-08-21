import requests
import time
import threading
from google_auth_oauthlib.flow import Flow
from google.cloud import storage_transfer
from google.cloud.exceptions import GoogleCloudError
from urllib.parse import urlparse, parse_qs, urlencode, quote, unquote

# Flask app base URL
SERVER_BASE_URL = "http://35.231.110.68:5001"

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
ENCRYPT_FILES = True
LOGS_URL = "https://console.cloud.google.com/functions/details/us-west2/StorageTransferFunction?env=gen2&project=backup-428118&tab=logs"
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds
SERVICE_ACCOUNT_EMAIL = "backuptransfer@backup-428118.iam.gserviceaccount.com"
PROJECT_ID = "backup-428118"
DESCRIPTION = "Archive Org data export"
AGENT_POOL_NAME="projects/backup-428118/agentPools/sts"
# Stages to monitor
STAGES = ["compression", "encryption", "drive_upload"]

# credentials = service_account.Credentials.from_service_account_file(
#     'backup-transfer.json'
# )

def start_process(folder_name):
    """Send a request to start processing the folder."""
    url = f"{SERVER_BASE_URL}/process"
    response = requests.post(url, json={"folder_name": DESTINATION_FOLDER + folder_name})
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

def monitor_progress():
    """Monitor and print the progress of each stage every 5 seconds."""
    start_time = time.time()

    while True:
        all_stages_completed = True
        progress_status = []

        for stage in STAGES:
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

def create_transfer_job(
    credentials,
    source_bucket: str,
):
    """Create migration job from a GCS bucket to a Nearline GCS bucket."""


    client = storage_transfer.StorageTransferServiceClient(credentials=credentials)

    transfer_job_request = storage_transfer.CreateTransferJobRequest(
        {
            "transfer_job": {
                "project_id": PROJECT_ID,
                "description": DESCRIPTION,
                "status": storage_transfer.TransferJob.Status.ENABLED,
                "transfer_spec": {
                    "gcs_data_source": {
                        "bucket_name": source_bucket,
                    },
                    "posix_data_sink": {
                        "root_directory": DESTINATION_FOLDER + source_bucket,
                    },
                    "transfer_options": {
                        "delete_objects_from_source_after_transfer": False
                    },
                    "sink_agent_pool_name" : AGENT_POOL_NAME
                },
            }
        }
    )

    result = client.create_transfer_job(transfer_job_request)
    print(f"Created transferJob: {result.name}")
    return result # Return the job name


def run_transfer_job(credentials, job_name):
    """Runs the specified transfer job."""
    client = storage_transfer.StorageTransferServiceClient(credentials=credentials)

    try:
        job_run = client.run_transfer_job({'job_name': job_name, "project_id": PROJECT_ID})
        print(f"Started transfer job: {job_name}")
        return job_run
    except GoogleCloudError as e:
        print(f"Error running transfer job: {e}")

def get_transfer_job_status(credentials, job_name):
    """Gets the status of the specified transfer job."""
    client = storage_transfer.StorageTransferServiceClient(credentials=credentials)

    try:
        job = client.get_transfer_job({'job_name': job_name, "project_id": PROJECT_ID})
        latest_operation_name = job.latest_operation_name
        print('Fetching operation')
        op = client.get_operation()
        print(f"Transfer job latest_operation_name: {latest_operation_name}")
        return op
    except GoogleCloudError as e:
        print(f"Error getting transfer job status: {e}")
        return None  # Or handle the error as appropriate

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

def main(request):
    """Entry point for the cloud function."""
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

    def background_task(auth_code, folder_name):
        """Run the processing task in the background"""
        try:
            credentials = fetch_credentials(auth_code)

            # Call the create_folder endpoint
            create_folder(folder_name)
            # Download archive to GCP server
            job = create_transfer_job(credentials, folder_name)
            job_run = run_transfer_job(credentials, job.name)
            while not job_run.done():
                # operation = get_transfer_job_status(credentials, job.name)
                print("Downloading archive...")
                time.sleep(60)
            print("Download completed successfully!")
            # Start Compression, Encryption and Drive Upload Process
            if start_process(folder_name):
                monitor_progress()
        except Exception as e:
            print(f"task failed: {e}")    

    threading.Thread(target=background_task, args=(auth_code, folder_name)).start()
    
    # Manually set the headers for HTTP redirect
    return '', 302, {'Location': LOGS_URL}

if __name__ == "__main__":
    main('test')