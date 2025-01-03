import os
import time
import threading
import google.auth

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from tqdm import tqdm


# Constants
CHUNK_SIZE = 256 * 1024 * 1024  # 256MB chunks
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds
PROJECT_ID = "backup-landnat"
ADC_SECRET_FILE = 'adc.json'
SOURCE_BUCKET_NAME = 'takeout-export-1e9e9a5d-6383-41c9-9e7a-c92184ff46e2'  # Your source bucket
DESTINATION_BUCKET_NAME = 'gws-landnet-backup'  # Your destination bucket


# Dictionary to track progress
progress_tracker = {
    "upload": 0,
}
progress_lock = threading.Lock()

def update_progress(stage, progress):
    with progress_lock:
        progress_tracker[stage] = progress


def get_adc_credentials():
    """Get default application credentials"""
    # Set the GOOGLE_APPLICATION_CREDENTIALS environment variable
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ADC_SECRET_FILE

    # Fetch Application Default Credentials
    credentials, project = google.auth.default()
    return credentials


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


#@retry(Exception)
def upload(credentials, source_folder_name, destination_folder_name):
    """Upload files from one Google Cloud Storage bucket to another."""

    try:
        storage_client = storage.Client(credentials=credentials, project=PROJECT_ID)
        
        # Source bucket
        source_bucket = storage_client.bucket(SOURCE_BUCKET_NAME)
        
        # Destination bucket
        destination_bucket = storage_client.bucket(DESTINATION_BUCKET_NAME)

        blobs = list(source_bucket.list_blobs())
        total_blobs = len(blobs)

        # Initialize tqdm progress bar
        with tqdm(total=total_blobs, desc="Uploading files", unit="file") as pbar:
            for i, blob in enumerate(blobs, start=1):
                # Construct the destination blob name
                destination_blob_name = f"{source_folder_name}/{blob.name.split(source_folder_name + '/')[-1]}" 

                # Copy the blob to the destination bucket
                source_bucket.copy_blob(blob, destination_bucket, destination_blob_name)

                # Update tqdm progress bar
                pbar.update(1)

        update_progress("upload", 100)
        return f"Successfully uploaded {total_blobs} files to {DESTINATION_BUCKET_NAME}"

    except Exception as e:
        print(f"Error during upload: {e}")
        raise


def process(source_folder_name, destination_folder_name):
    """Process files in a folder, including upload."""
    print(f'Starting process for folder: {source_folder_name}')

    try:
        # Upload folder from source bucket to destination bucket
        upload_credentials = get_adc_credentials()
        upload_status = upload(upload_credentials, source_folder_name, destination_folder_name)
        print(upload_status)
        print(f'Successfully processed folder: {source_folder_name}')
        return (f'Success: Folder {source_folder_name} processed', 200)

    except GoogleCloudError as e:
        print(f"Error interacting with Google Cloud Storage: {e}")
        return ('Error interacting with Google Cloud Storage', 500)
    except OSError as e:
        print(f"File system error: {e}")
        return ('File system error occurred', 500)
    except Exception as e:
        print(f"An error occurred: {e}")
        return ('An error occurred during processing', 500)


if __name__ == '__main__':
    process(SOURCE_BUCKET_NAME, DESTINATION_BUCKET_NAME)
