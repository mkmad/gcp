import os
import subprocess
import threading
import requests
import zipfile
from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from google_auth_oauthlib.flow import Flow
from google.cloud.exceptions import GoogleCloudError
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from tqdm import tqdm
from urllib.parse import urlparse, parse_qs, urlencode, quote, unquote
import time


# Constants
DESTINATION_BUCKET_NAME = 'rowhousebackup'
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
        result = subprocess.run(['gpg', '--yes', '--import', public_key_file], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            raise subprocess.CalledProcessError(result.returncode, result.args)
    except Exception as e:
        print(f"Failed to import public key: {e}")
        raise

@retry(Exception)
def encrypt_chunk(file_path, recipient_email, chunk_number, chunk_data):
    """Encrypt a chunk of the file with the public key"""
    chunk_file_path = f"{file_path}.part{chunk_number}.gpg"
    try:
        process = subprocess.Popen([
            'gpg', '--yes', '--always-trust', '--output', chunk_file_path,
            '--encrypt', '--recipient', recipient_email
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        stdout, stderr = process.communicate(input=chunk_data)
        print(stdout.decode())
        if process.returncode != 0:
            print(stderr.decode())
            raise subprocess.CalledProcessError(process.returncode, process.args)
    except Exception as e:
        print(f"Failed to encrypt chunk {chunk_number}: {e}")
        raise
    return chunk_file_path

def encrypt_file_in_chunks(file_path, recipient_email):
    """Encrypt a file in chunks"""
    encrypted_chunk_paths = []
    file_size = os.path.getsize(file_path)
    total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE  # Calculate total number of chunks
    with open(file_path, 'rb') as f:
        chunk_number = 0
        while True:
            chunk_data = f.read(CHUNK_SIZE)
            if not chunk_data:
                break
            encrypted_chunk_paths.append(encrypt_chunk(file_path, recipient_email, chunk_number, chunk_data))
            chunk_number += 1
            
    combined_encrypted_path = f"{file_path}.gpg"
    with open(combined_encrypted_path, 'wb') as combined_file:
        for chunk_path in encrypted_chunk_paths:
            with open(chunk_path, 'rb') as chunk_file:
                combined_file.write(chunk_file.read())
            os.remove(chunk_path)
    
    return combined_encrypted_path

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

@retry(Exception)
def download_part(url, headers, start, end, dest_path, part_num):
    headers['Range'] = f"bytes={start}-{end}"
    response = requests.get(url, headers=headers, stream=True)
    part_path = f"{dest_path}.part{part_num}"
    with open(part_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return part_path

def combine_parts(dest_path, num_parts):
    with open(dest_path, 'wb') as dest_file:
        for part_num in range(num_parts):
            part_path = f"{dest_path}.part{part_num}"
            with open(part_path, 'rb') as part_file:
                dest_file.write(part_file.read())
            os.remove(part_path)

def download_with_multipart(blob, destination_path, chunk_size=10*1024*1024):
    headers = {"Authorization": f"Bearer {blob.client._credentials.token}"}
    url = f"https://storage.googleapis.com/{blob.bucket.name}/{blob.name}"
    file_size = blob.size
    num_parts = (file_size // chunk_size) + int(file_size % chunk_size > 0)
    
    with tqdm(total=file_size, desc=f"Downloading {os.path.basename(destination_path)}", unit="B", unit_scale=True) as pbar:
        part_paths = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(download_part, url, headers, part_num * chunk_size, min((part_num + 1) * chunk_size - 1, file_size - 1), destination_path, part_num)
                for part_num in range(num_parts)
            ]
            for future in futures:
                part_paths.append(future.result())
                pbar.update(chunk_size if future.result() else file_size - pbar.n)
    
    combine_parts(destination_path, num_parts)

@retry(Exception)
def compress_file(file_path):
    zip_filename = f"{file_path}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.write(file_path, os.path.basename(file_path))
    return zip_filename

def compress_files_in_folder_multiprocessing(folder_name):
    folder_path = f"/tmp/{folder_name}"
    os.makedirs(folder_path, exist_ok=True)

    zip_filename = f"/tmp/{folder_name}.zip"
    files_to_compress = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            files_to_compress.append(os.path.join(root, file))

    total_files = len(files_to_compress)

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(compress_file, file_path) for file_path in files_to_compress]
        with tqdm(total=total_files, desc="Compressing files", unit="file") as pbar:
            for future in futures:
                future.result()
                pbar.update(1)

    # Combine all the small zip files into one big zip file
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as final_archive:
        for future in futures:
            zip_file = future.result()
            final_archive.write(zip_file, os.path.basename(zip_file))
            os.remove(zip_file)
    return zip_filename

@retry(Exception)
def upload_file_to_drive(file_path, file_name, folder_id, credentials):
    """Upload file to Google Drive"""
    try:
        credentials_, project = default()
        credentials_ = credentials_.with_scopes(['https://www.googleapis.com/auth/drive'])        
        service = build('drive', 'v3', credentials=credentials_)
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaFileUpload(file_path, chunksize=CHUNK_SIZE, resumable=True)
        request = service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True)

        file_size = os.path.getsize(file_path)
        response = None
        with tqdm(total=file_size, desc="Uploading to Drive", unit="B", unit_scale=True) as pbar:
            while response is None:
                status, response = request.next_chunk()
                if status:
                    pbar.update(status.resumable_progress)

        print("Transfer complete")
        return response.get('id')
    except Exception as e:
        print(f"Error during upload to Google Drive: {e}")
        raise

def upload_zip_to_drive(zip_filename, folder_name, credentials):
    """Upload zip file to Google Drive"""
    try:
        drive_file_id = upload_file_to_drive(zip_filename, f"{folder_name}.zip", DRIVE_FOLDER_ID, credentials)
        print(f"Folder {folder_name} uploaded to Google Drive with ID: {drive_file_id}")
    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")
        raise

def process(credentials, folder_name):
    """Process files in a folder, including download, compress, encrypt, and upload."""
    print(f'Starting process for folder: {folder_name}')
    try:
        client = storage.Client(credentials=credentials)
        bucket = client.bucket(folder_name)
        blobs = list(bucket.list_blobs())

        if not blobs:
            print(f'Error: No files found in folder {folder_name}')
            return (f'Error: No files found in folder {folder_name}', 404)

        folder_path = f"/tmp/{folder_name}"
        os.makedirs(folder_path, exist_ok=True)

        # Download folder
        def download_files_from_bucket(blobs, folder_name, folder_path):
            print(f'Downloading files from bucket: {folder_name}')
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(download_with_multipart, blob, f"{folder_path}/{os.path.basename(blob.name)}")
                    for blob in blobs
                ]
                for future in futures:
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Error occurred: {e}")

        download_files_from_bucket(blobs, folder_name, folder_path)

        # Compress folder
        zip_filename = compress_files_in_folder_multiprocessing(folder_name)
        print(f"Compressed file: {zip_filename}")

        # Encrypt files
        if ENCRYPT_FILES:
            import_public_key(PUBLIC_KEY_FILE)                    
            encrypted_file_path = encrypt_file_in_chunks(zip_filename, RECIPIENT_EMAIL)
            print(f"Encrypted file to {encrypted_file_path}")
            upload_path = encrypted_file_path
        else:
            upload_path = zip_filename

        # Upload zip file to google drive
        print(f"Uploading {upload_path} to Google Drive in folder {DRIVE_FOLDER_ID}")
        upload_zip_to_drive(upload_path, folder_name, credentials)

        # Cleanup all files
        print(f'Cleaning up temporary files')
        os.remove(zip_filename)
        for root, _, files in os.walk(folder_path):
            for file in files:
                os.remove(os.path.join(root, file))
        os.removedirs(folder_path)

        print(f'Successfully processed folder: {folder_name}')
        return (f'Success: Folder {folder_name} processed', 200)

    except DefaultCredentialsError as e:
        print(f"Error retrieving credentials: {e}")
        return ('Error retrieving credentials', 500)
    except GoogleCloudError as e:
        print(f"Error interacting with Google Cloud Storage: {e}")
        return ('Error interacting with Google Cloud Storage', 500)
    except OSError as e:
        print(f"File system error: {e}")
        return ('File system error occurred', 500)
    except Exception as e:
        print(f"An error occurred: {e}")
        return ('An error occurred during processing', 500)

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

    response_message = (
        f"<html><body>"
        f"<p>Processing for folder '<strong>{folder_name}</strong>' has started. Check the logs for progress updates.</p>"
        f"<p>Click on this link to watch for logs: "
        f"<a href=\"{LOGS_URL}\" style=\"color: blue; text-decoration: underline;\">Watch Logs</a></p>"
        f"</body></html>"
    )

    def background_task(auth_code, folder_name):
        """Run the processing task in the background"""
        try:
            credentials = fetch_credentials(auth_code)
            process(credentials, folder_name)
        except Exception as e:
            print(f"Background task failed: {e}")

    threading.Thread(target=background_task, args=(auth_code, folder_name)).start()
    
    return response_message, 200, {'Content-Type': 'text/plain'}
