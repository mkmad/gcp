import json
import os
import time
import shutil
import subprocess
import threading
import zipfile
import google.auth

from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from google.cloud import storage
from google.cloud.storage import transfer_manager
from google.cloud.exceptions import GoogleCloudError
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from tqdm import tqdm
from google_auth_oauthlib.flow import Flow

app = Flask(__name__)

# Constants
DRIVE_FOLDER_ID = '0AEKStjCq23zkUk9PVA'
CHUNK_SIZE = 256 * 1024 * 1024  # 256MB chunks
PUBLIC_KEY_FILE = 'test.asc'
RECIPIENT_EMAIL = 'technology@xponential.com'
ENCRYPT_FILES = True
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds
DESTINATION_FOLDER = './'
PROJECT_ID = "backup-428118"
ADC_SECRET_FILE = 'rowhouse-creds.json'
CLIENT_SECRETS_FILE = 'client_secret.json'
SERVICE_ACCOUNT_FILE = 'backup-transfer.json'

SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform', 
    'https://www.googleapis.com/auth/drive'
]
REDIRECT_URI = 'https://us-west2-backup-428118.cloudfunctions.net/StorageTransferFunction'


# Dictionary to track progress
progress_tracker = {
    "download": 0,
    "compression": 0,
    "encryption": 0,
    "drive_upload": 0,
}
progress_lock = threading.Lock()

def update_progress(stage, progress):
    with progress_lock:
        progress_tracker[stage] = progress

from google.oauth2 import service_account

def get_service_account_credentials():
    # Path to the service account file
    service_account_file = SERVICE_ACCOUNT_FILE

    # Create credentials from the service account file
    credentials = service_account.Credentials.from_service_account_file(service_account_file)
    
    return credentials

def get_adc_credentials():
    # Set the GOOGLE_APPLICATION_CREDENTIALS environment variable
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ADC_SECRET_FILE

    # Fetch Application Default Credentials
    credentials, project = google.auth.default()
    return credentials

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

def retry(exceptions, max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Decorator for retrying a function call with specified exceptions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    if attempt + 1 == max_retries:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

def import_public_key(public_key_file):
    """Import public key"""
    print(f"Importing public key from {public_key_file}")
    try:
        result = subprocess.run(['sudo', 'gpg', '--yes', '--import', public_key_file], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            raise subprocess.CalledProcessError(result.returncode, result.args)
    except Exception as e:
        print(f"Failed to import public key: {e}")
        raise

@retry(Exception)
def decrypt_file(file_path, recipient_email):
    """Encrypt a chunk of the file with the public key"""
    try:
        result = subprocess.run([
            'sudo', 'gpg', '--yes', '--always-trust', '--output', file_path,
            '--decrypt', '--recipient', recipient_email
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            raise subprocess.CalledProcessError(result.returncode, result.args)
    except Exception as e:
        print(f"Failed to decrypt file: {e}")
        raise


@retry(Exception)
def encrypt_file(file_path):
    """Encrypt the file with the public key"""
    encrypted_file_path = f"{file_path}.gpg"
    file_size = os.path.getsize(file_path)
    
    # Use tqdm to show progress
    with open(file_path, 'rb') as f, open(encrypted_file_path, 'wb') as enc_file:
        process = subprocess.Popen([
            'sudo', 'gpg', '--yes', '--always-trust', '--encrypt', '--recipient', RECIPIENT_EMAIL
        ], stdin=subprocess.PIPE, stdout=enc_file, stderr=subprocess.PIPE)
        
        # Use tqdm to display a progress bar
        with tqdm(total=file_size, unit='B', unit_scale=True, desc="Encrypting") as pbar:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                process.stdin.write(chunk)
                pbar.update(len(chunk))
                
                # Calculate and update the progress percentage
                progress_percent = int((pbar.n / file_size) * 100)
                update_progress("encryption", progress_percent)
        
        process.stdin.close()
        process.wait()
        
        if process.returncode != 0:
            stderr = process.stderr.read().decode()
            print(stderr)
            raise subprocess.CalledProcessError(process.returncode, process.args)
        
    # Ensure progress is marked as 100% at the end
    update_progress("encryption", 100)
    return encrypted_file_path

@retry(Exception)
def add_file_to_zip(zip_filename, file_path):
    with zipfile.ZipFile(zip_filename, 'a', zipfile.ZIP_DEFLATED) as archive:
        archive.write(file_path, os.path.basename(file_path))

def compress_files_in_folder(folder_name):
    folder_path = f"{folder_name}"
    os.makedirs(folder_path, exist_ok=True)

    zip_filename = f"{folder_name}.zip"
    files_to_compress = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            files_to_compress.append(os.path.join(root, file))

    total_files = len(files_to_compress)

    with tqdm(total=total_files, desc="Compressing files", unit="file") as pbar:
        for i, file_path in enumerate(files_to_compress):
            add_file_to_zip(zip_filename, file_path)
            pbar.update(1)
            update_progress("compression", int(((i + 1) / total_files) * 100))

    update_progress("compression", 100)
    return zip_filename

@retry(Exception)
def upload_file_to_drive(file_path, file_name, folder_id, credentials):
    """Upload file to Google Drive"""
    try:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ""
        service = build('drive', 'v3', credentials=credentials)
        file_metadata = {'name': file_name.split('/')[-1], 'parents': [folder_id]}
        media = MediaFileUpload(file_path, chunksize=CHUNK_SIZE, resumable=True)
        request = service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True)

        file_size = os.path.getsize(file_path)
        response = None
        uploaded_size = 0
        with tqdm(total=file_size, desc="Uploading to Drive", unit="B", unit_scale=True) as pbar:
            while response is None:
                status, response = request.next_chunk()
                if status:
                    uploaded_size += status.resumable_progress
                    pbar.update(status.resumable_progress)
                    progress = int((uploaded_size / file_size) * 100)
                    if progress < 100:
                        update_progress("drive_upload", progress)
        update_progress("drive_upload", 100)
        return response.get('id')
    except Exception as e:
        print(f"Error during upload to Google Drive: {e}")
        raise

#@retry(Exception)
def download(credentials, folder_name):
    """Download a folder from Google Cloud Storage using transfer_manager."""

    try:
        storage_client = storage.Client(credentials=credentials, project=PROJECT_ID)
        destination_directory = os.path.join(DESTINATION_FOLDER, folder_name)        
        bucket = storage_client.bucket(folder_name)
        blob_names = [blob.name for blob in bucket.list_blobs()]
        total_blobs = len(blob_names)

        transfer_manager.download_many_to_path(
            bucket, blob_names, destination_directory=destination_directory, max_workers=8
        )

        for i, name in enumerate(blob_names, start=1):
            update_progress("download", int((i / total_blobs) * 100))
        
        update_progress("download", 100)
        return destination_directory

    except Exception as e:
        print(f"Error during download: {e}")
        raise

def process(credentials, folder_name, auth_code, encryption):
    """Process files in a folder, including download, compress, encrypt, and upload."""
    print(f'Starting process for folder: {folder_name}')
    try:
        # Download folder from cloud storage
        download_credentials = get_adc_credentials()        
        download_folder_path = download(download_credentials, folder_name)
        print(f"Downloaded folder to {download_folder_path}")

        # Compress folder
        zip_filename = compress_files_in_folder(download_folder_path)
        print(f"Compressed file: {zip_filename}")
        # Remove folder after compression to save space
        shutil.rmtree(download_folder_path)

        # Encrypt files
        if encryption:
            import_public_key(PUBLIC_KEY_FILE)
            encrypted_file_path = encrypt_file(zip_filename)
            print(f"Encrypted file to {encrypted_file_path}")
            upload_path = encrypted_file_path
        else:
            upload_path = zip_filename
            update_progress("encryption", 100)

        # Upload zip file to google drive
        print(f"Uploading {upload_path} to Google Drive in folder {DRIVE_FOLDER_ID}")
        download_credentials = get_service_account_credentials()
        drive_file_id = upload_file_to_drive(upload_path, f"{folder_name}", DRIVE_FOLDER_ID, download_credentials)
        print(f"Folder {folder_name} uploaded to Google Drive with ID: {drive_file_id}")
        update_progress("drive_upload", 100)

        # Cleanup all files
        print(f'Cleaning up temporary files')
        # Check if the file exists before attempting to remove it
        if os.path.exists(upload_path):
            os.remove(upload_path)
            print(f'Removed {upload_path}')

        if os.path.exists(zip_filename):
            os.remove(zip_filename)
            print(f'Removed {zip_filename}')

        print(f'Successfully processed folder: {folder_name}')
        return (f'Success: Folder {folder_name} processed', 200)

    except GoogleCloudError as e:
        print(f"Error interacting with Google Cloud Storage: {e}")
        return ('Error interacting with Google Cloud Storage', 500)
    except OSError as e:
        print(f"File system error: {e}")
        return ('File system error occurred', 500)
    except Exception as e:
        print(f"An error occurred: {e}")
        return ('An error occurred during processing', 500)

@app.route('/process', methods=['POST'])
def process_folder():
    folder_name = request.json.get('folder_name')
    credentials_json = request.json.get('credentials')
    auth_code = request.json.get('auth_code')
    encryption = request.json.get('encryption')
    # Validate params
    if folder_name is None:
        return jsonify({'error': 'Folder name is required'}), 400
    if credentials_json is None:
        return jsonify({'error': 'Credentials are required'}), 400
    if auth_code is None:
        return jsonify({'error': 'auth_code is required'}), 400
    if encryption is None:
        return jsonify({'error': 'encryption is required'}), 400

    # Parse the credentials JSON string into a dictionary
    credentials_dict = json.loads(credentials_json)
    # Recreate the credentials object
    credentials = Credentials.from_authorized_user_info(credentials_dict)

    # Reset progress before starting
    with progress_lock:
        for key in progress_tracker.keys():
            progress_tracker[key] = 0

    # Start the processing in a separate thread
    threading.Thread(target=process, args=(credentials, folder_name, auth_code, encryption)).start()

    return jsonify({'message': f'Processing started for folder {folder_name}'}), 202

@app.route('/status/<stage>', methods=['GET'])
def status(stage):
    """Return the progress of the given stage."""
    if stage in progress_tracker:
        return jsonify({stage: progress_tracker[stage]}), 200
    else:
        return jsonify({'error': f'Stage {stage} not found'}), 404

@app.route('/create_folder', methods=['POST'])
def create_folder():
    folder_name = request.json.get('folder_name')
    if not folder_name:
        return jsonify({'error': 'Folder name is required'}), 400
    
    # Check if the folder already exists
    if os.path.exists(DESTINATION_FOLDER + folder_name):
        return jsonify({'message': f'Folder {folder_name} already exists'}), 200
    
    print(f"Folder {folder_name} does not exist. Creating")
    # Create the folder
    try:
        os.makedirs(DESTINATION_FOLDER + folder_name)
        print(f"Folder {folder_name} created successfully")
        return jsonify({'message': f'Folder {folder_name} created successfully'}), 201
    
    except OSError as e:
        print(f"Error creating folder {folder_name}: {e}")
        return jsonify({'error': f'Error creating folder {folder_name}: {e}'}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
    #process('', 'upload-test1', '')
