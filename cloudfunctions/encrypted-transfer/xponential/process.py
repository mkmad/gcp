import os
import time
import shutil
import subprocess
import tarfile
import threading
import zipfile

from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from google.oauth2 import service_account
from google.cloud.exceptions import GoogleCloudError
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from tqdm import tqdm

app = Flask(__name__)

# Constants
DRIVE_FOLDER_ID = '0AEKStjCq23zkUk9PVA'
CHUNK_SIZE = 256 * 1024 * 1024  # 256MB chunks
PUBLIC_KEY_FILE = 'test.asc'
RECIPIENT_EMAIL = 'technology@xponential.com'
ENCRYPT_FILES = True
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds
SERVICE_ACCOUNT_FILE = 'backup-transfer.json'
DESTINATION_FOLDER='/root/'

# Dictionary to track progress
progress_tracker = {
    "compression": 0,
    "encryption": 0,
    "drive_upload": 0
}
progress_lock = threading.Lock()

def update_progress(stage, progress):
    with progress_lock:
        progress_tracker[stage] = progress

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
def encrypt_chunk(file_path, recipient_email, chunk_number, chunk_data):
    """Encrypt a chunk of the file with the public key"""
    chunk_file_path = f"{file_path}.part{chunk_number}.gpg"
    try:
        process = subprocess.Popen([
            'sudo', 'gpg', '--yes', '--always-trust', '--output', chunk_file_path,
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
            update_progress("encryption", int((chunk_number / total_chunks) * 100))
            
    combined_encrypted_path = f"{file_path}.gpg"
    with open(combined_encrypted_path, 'wb') as combined_file:
        for chunk_path in encrypted_chunk_paths:
            with open(chunk_path, 'rb') as chunk_file:
                combined_file.write(chunk_file.read())
            os.remove(chunk_path)
    
    return combined_encrypted_path

@retry(Exception)
def compress_file(file_path):
    zip_filename = f"{file_path}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.write(file_path, os.path.basename(file_path))
    return zip_filename

def compress_files_in_folder_multiprocessing(folder_name):
    folder_path = f"{folder_name}"
    os.makedirs(folder_path, exist_ok=True)

    zip_filename = f"{folder_name}.zip"
    files_to_compress = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            files_to_compress.append(os.path.join(root, file))

    total_files = len(files_to_compress)

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(compress_file, file_path) for file_path in files_to_compress]
        with tqdm(total=total_files, desc="Compressing files", unit="file") as pbar:
            for i, future in enumerate(futures):
                future.result()
                pbar.update(1)
                update_progress("compression", int(((i + 1) / total_files) * 100))

    # Combine all the small zip files into one big zip file
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as final_archive:
        for future in futures:
            zip_file = future.result()
            final_archive.write(zip_file, os.path.basename(zip_file))
            os.remove(zip_file)
    update_progress("compression", 100)
    return zip_filename

@retry(Exception)
def upload_file_to_drive(file_path, file_name, folder_id, credentials):
    """Upload file to Google Drive"""
    try:
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
        return response.get('id')
    except Exception as e:
        print(f"Error during upload to Google Drive: {e}")
        raise

def process(credentials, folder_name):
    """Process files in a folder, including download, compress, encrypt, and upload."""
    print(f'Starting process for folder: {folder_name}')
    try:

        # Compress folder
        zip_filename = compress_files_in_folder_multiprocessing(folder_name)
        print(f"Compressed file: {zip_filename}")
        # Remove folder after compression to save space
        shutil.rmtree(folder_name)

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
        drive_file_id = upload_file_to_drive(upload_path, f"{folder_name}.zip.gpg", DRIVE_FOLDER_ID, credentials)
        print(f"Folder {folder_name} uploaded to Google Drive with ID: {drive_file_id}")        
        update_progress("drive_upload", 100)

        # Cleanup all files
        print(f'Cleaning up temporary files')
        os.remove(upload_path)
        os.remove(zip_filename)

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
    if not folder_name:
        return jsonify({'error': 'Folder name is required'}), 400
    
    # Check if the folder exists
    if not os.path.exists(folder_name):
        print(f"Folder {folder_name} does not exist.")
        return (f'Error: Folder {folder_name} does not exist', 404)    
    
    # Load credentials from the service account file
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)

    # Reset progress before starting
    with progress_lock:
        for key in progress_tracker.keys():
            progress_tracker[key] = 0

    # Start the processing in a separate thread
    threading.Thread(target=process, args=(credentials, folder_name)).start()

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
    app.run(host='0.0.0.0', port=5001)
