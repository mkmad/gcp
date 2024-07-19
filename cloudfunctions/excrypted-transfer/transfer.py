import os
import subprocess
from tqdm import tqdm
import time

# Encryption Metadata
PUBLIC_KEY_FILE = 'test.asc'  # Path to your public key file
RECIPIENT_EMAIL = 'technology@xponential.com'  # Change to the recipient's email associated with the public key
INPUT_FILE = 'test.txt'

def import_public_key(public_key_file):
    print(f"Importing public key from {public_key_file}")
    subprocess.run(['gpg', '--import', public_key_file], check=True)

def encrypt_file(file_path, recipient_email):
    encrypted_file_path = f"{file_path}.gpg"
    print(f"Encrypting file {file_path} to {encrypted_file_path} for recipient {recipient_email}")

    # Start the encryption process
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
        
        # Ensure the progress bar completes
        if os.path.exists(encrypted_file_path):
            final_size = os.path.getsize(encrypted_file_path)
            pbar.update(final_size - pbar.n)
    
    stdout, stderr = process.communicate()
    print(stdout)
    if process.returncode != 0:
        print(stderr)
        raise subprocess.CalledProcessError(process.returncode, process.args)
    return encrypted_file_path

def list_files_in_directory(directory):
    files = os.listdir(directory)
    print(f"Files in {directory}: {files}")
    return files

def main():
    # Initialize progress bar
    try:
        import_public_key(PUBLIC_KEY_FILE)        
        encrypt_file(INPUT_FILE, RECIPIENT_EMAIL)        
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()
