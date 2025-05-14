#!/bin/bash

# Script to simulate SSH brute force attempts for testing Google Cloud SCC detection
# Simulates multiple failed login attempts to trigger a "Brute Force: SSH" finding

# Configuration
TARGET_HOST="35.226.149.244"  # Target VM's external IP
TARGET_USER="ubuntu"        # Temporary test user (create this user first)
CORRECT_PASSWORD="******"  # Strong temporary password
ATTEMPTS=50                   # Number of failed attempts (adjust as needed)
SSH_PORT=22                   # Default SSH port
SOURCE_IP=$(curl -s ifconfig.me)  # Get source machine's public IP

# Check dependencies
if ! command -v sshpass &> /dev/null; then
    echo "Error: sshpass is required. Install with 'sudo apt-get install sshpass' (Ubuntu/Debian)."
    exit 1
fi
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud SDK is required. Install from https://cloud.google.com/sdk."
    exit 1
fi

# Validate inputs
if [ -z "$TARGET_HOST" ] || [ -z "$TARGET_USER" ] || [ -z "$CORRECT_PASSWORD" ]; then
    echo "Error: TARGET_HOST, TARGET_USER, and CORRECT_PASSWORD must be set."
    exit 1
fi

# Verify SSH password authentication on target VM
echo "Verifying SSH configuration on $TARGET_HOST..."
ssh -o BatchMode=yes -o ConnectTimeout=5 -p "$SSH_PORT" "$TARGET_USER@$TARGET_HOST" true 2>&1 | grep -q "PasswordAuthentication"
if [ $? -eq 0 ]; then
    echo "Error: Password authentication may be disabled on the target VM."
    echo "Run 'sudo sed -i \"s/PasswordAuthentication no/PasswordAuthentication yes/\" /etc/ssh/sshd_config' and 'sudo systemctl restart sshd' on the VM."
    exit 1
fi

# Verify firewall rules
echo "Checking firewall rules for port $SSH_PORT..."
gcloud compute firewall-rules list --filter="name~default-allow-ssh" --format="value(ALLOW,SOURCE_RANGES)" | grep -q "$SSH_PORT"
if [ $? -ne 0 ]; then
    echo "Error: No firewall rule allows SSH (port $SSH_PORT). Create one with:"
    echo "gcloud compute firewall-rules create default-allow-ssh --allow=tcp:$SSH_PORT --source-ranges=$SOURCE_IP/32 --enable-logging"
    exit 1
fi


# Warn about security risks
echo "WARNING: This script simulates SSH brute force attempts on $TARGET_HOST."
echo "Ensure the VM is isolated (e.g., firewall restricts access to $SOURCE_IP)."
echo "Use a temporary test user and strong password. Clean up after testing."
read -p "Continue? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Function to attempt SSH login
attempt_ssh() {
    local password="$1"
    local attempt_num="$2"
    echo "Attempt $attempt_num: Trying password '$password'..."
    
    # Use sshpass with explicit password prompt and relaxed options
    sshpass -p "$password" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        -o PreferredAuthentications=password -o PubkeyAuthentication=no \
        -p "$SSH_PORT" "$TARGET_USER@$TARGET_HOST" "exit 0" 2>/dev/null
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "Attempt $attempt_num: SUCCESS"
    else
        echo "Attempt $attempt_num: FAILED (Exit code: $exit_code)"
    fi
    return $exit_code
}

# Simulate failed attempts
for ((i=1; i<=ATTEMPTS; i++)); do
    # Generate a random wrong password
    wrong_password="wrong$(openssl rand -hex 4)"
    attempt_ssh "$wrong_password" "$i"
    # Random delay to mimic real brute force
    sleep $((RANDOM % 2))
done

#Optional: Simulate successful attempt (uncomment if needed)
echo "Attempt $((ATTEMPTS+1)): Trying correct password..."
attempt_ssh "$CORRECT_PASSWORD" "$((ATTEMPTS+1))"

# # Clean up (optional: disable password authentication)
# echo "Cleaning up..."
# ssh -o StrictHostKeyChecking=no -p "$SSH_PORT" "$TARGET_USER@$TARGET_HOST" \
#     "sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config && sudo systemctl restart sshd" 2>/dev/null
# echo "Password authentication disabled on target VM."

# Instructions for next steps
echo "Simulation complete. Wait up to 15 minutes and check SCC for 'Brute Force: SSH' finding:"
echo "1. Go to Google Cloud Console -> Security Command Center -> Findings."
echo "2. Filter for 'Brute Force: SSH' (sourceIp: $SOURCE_IP)."
echo "3. Check /var/log/auth.log on the target VM for login attempts."
echo "4. Delete the test user: 'sudo userdel -r $TARGET_USER' on the VM."
echo "5. Delete the test VM if no longer needed: 'gcloud compute instances delete <instance-name>'."