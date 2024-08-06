import functions_framework
import google.auth
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.cloud import storage
from concurrent.futures import ThreadPoolExecutor
import os
import subprocess
import time
from tqdm import tqdm

# Set this to the drive folder ID
DRIVE_FOLDER_ID = '0AEKStjCq23zkUk9PVA'
CHUNK_SIZE = 256 * 1024 * 1024  # 256MB chunks
PUBLIC_KEY_FILE = 'xponential_public.asc'  # Path to your public key file
RECIPIENT_EMAIL = 'technology@xponential.com'  # Change to the recipient's email associated with the public key
ENCRYPT_FILES = True  # Global flag to determine if files need to be encrypted before uploading

def import_public_key(public_key_file):
    print(f"Importing public key from {public_key_file}")
    result = subprocess.run(['gpg', '--yes', '--import', public_key_file], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args)

def encrypt_file_with_public_key(file_path, recipient_email):
    encrypted_file_path = f"{file_path}.gpg"
    print(f"Encrypting file {file_path} to {encrypted_file_path} for recipient {recipient_email}")

    process = subprocess.Popen([
        'gpg', '--yes', '--always-trust', '--output', encrypted_file_path,
        '--encrypt', '--recipient', recipient_email, file_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    file_size = os.path.getsize(file_path)
    with tqdm(total=file_size, desc="Encrypting", unit="B", unit_scale=True) as pbar:
        while process.poll() is None:
            if os.path.exists(encrypted_file_path):
                current_size = os.path.getsize(encrypted_file_path)
                pbar.update(current_size - pbar.n)
            time.sleep(0.1)
        
        if os.path.exists(encrypted_file_path):
            final_size = os.path.getsize(encrypted_file_path)
            pbar.update(final_size - pbar.n)
    
    stdout, stderr = process.communicate()
    print(stdout)
    if process.returncode != 0:
        print(stderr)
        raise subprocess.CalledProcessError(process.returncode, process.args)
    return encrypted_file_path

def upload_to_drive(file_path, file_name, folder_id, credentials):
    try:
        service = build('drive', 'v3', credentials=credentials)
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, chunksize=CHUNK_SIZE, resumable=True)
        request = service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True)
        
        file_size = os.path.getsize(file_path)
        response = None
        with tqdm(total=file_size, desc="Uploading to Drive", unit="B", unit_scale=True) as pbar:
            while response is None:
                status, response = request.next_chunk()
                if status:
                    pbar.update(CHUNK_SIZE if status.resumable_progress else file_size - pbar.n)
        
        print("Transfer complete")
        return response.get('id')
    except Exception as e:
        print(f"Error during upload: {e}")
        return None

def process_file(bucket_name, file_name, credentials, recipient_email, encrypt_files):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    
    temp_file_path = f"/tmp/{file_name}"
    temp_file_dir = os.path.dirname(temp_file_path)
    if not os.path.exists(temp_file_dir):
        os.makedirs(temp_file_dir)
    
    print(f"Downloading {file_name} from bucket {bucket_name} to {temp_file_path}")
    blob.download_to_filename(temp_file_path)
    print(f"Download complete for {file_name}")

    if encrypt_files:
        encrypted_file_path = encrypt_file_with_public_key(temp_file_path, recipient_email)
        print(f"Encrypted {file_name} to {encrypted_file_path}")
        upload_path = encrypted_file_path
    else:
        upload_path = temp_file_path

    drive_file_id = upload_to_drive(upload_path, os.path.basename(upload_path), DRIVE_FOLDER_ID, credentials)
    
    if encrypt_files:
        if os.path.exists(encrypted_file_path):
            os.remove(encrypted_file_path)
            print(f"Deleted encrypted file {encrypted_file_path}")
        else:
            print(f"Encrypted file {encrypted_file_path} not found, skipping deletion")
        
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
        print(f"Deleted temporary file {temp_file_path}")
    else:
        print(f"Temporary file {temp_file_path} not found, skipping deletion")
    
    return drive_file_id

@functions_framework.cloud_event
def transfer_files(cloud_event):
    data = cloud_event.data

    event_id = cloud_event["id"]
    event_type = cloud_event["type"]

    bucket_name = data["bucket"]
    file_name = data["name"]

    print(f"Event ID: {event_id}")
    print(f"Event type: {event_type}")
    print(f"Bucket: {bucket_name}")
    print(f"File: {file_name}")

    credentials, project = google.auth.default()
    credentials = credentials.with_scopes(['https://www.googleapis.com/auth/drive'])

    if ENCRYPT_FILES:
        import_public_key(PUBLIC_KEY_FILE)

    print(f"{file_name} is recognized as a file.")
    with ThreadPoolExecutor() as executor:
        future = executor.submit(process_file, bucket_name, file_name, credentials, RECIPIENT_EMAIL, ENCRYPT_FILES)
        drive_file_id = future.result()
        print(f"File {file_name} uploaded to Google Drive with ID: {drive_file_id}")


# functions-framework
# google-auth==2.15.0
# google-auth-httplib2==0.1.0
# google-auth-oauthlib==0.4.6
# google-cloud-storage==2.5.0
# google-api-python-client==2.50.0
# tqdm==4.66.4