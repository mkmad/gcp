#!/bin/bash

# Script to simulate SSH brute force attempts for testing SCC detection
# Simulates 20 failed login attempts with wrong passwords, then 1 successful login

# Configuration
TARGET_HOST="34.122.29.119"  # Replace with your VM's external IP
TARGET_USER="ubuntu"          # Replace with your test user
CORRECT_PASSWORD="ubuntu321" # Replace with the actual password
ATTEMPTS=50                   # Number of failed attempts
SSH_PORT=22                   # Default SSH port

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "Error: sshpass is required. Install it with 'sudo apt-get install sshpass' (Ubuntu/Debian)."
    exit 1
fi

# Validate inputs
if [ -z "$TARGET_HOST" ] || [ -z "$TARGET_USER" ] || [ -z "$CORRECT_PASSWORD" ]; then
    echo "Error: TARGET_HOST, TARGET_USER, and CORRECT_PASSWORD must be set."
    exit 1
fi

# Warn about security risks
echo "WARNING: This script simulates SSH brute force attempts. Ensure the target VM is isolated (e.g., firewall restricts access to your IP)."
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
    
    # Use sshpass to attempt login, suppress output, and capture exit code
    sshpass -p "$password" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
        -p "$SSH_PORT" "$TARGET_USER@$TARGET_HOST" "echo 'Login successful'" 2>/dev/null
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
    # Generate a random wrong password (simple for testing)
    wrong_password="wrongpass$i"
    attempt_ssh "$wrong_password" "$i"
    # Small delay to mimic real brute force behavior
    sleep 1
done

# Simulate successful attempt
echo "Attempt $((ATTEMPTS+1)): Trying correct password..."
attempt_ssh "$CORRECT_PASSWORD" "$((ATTEMPTS+1))"

# Instructions for next steps
echo "Simulation complete. Wait up to 15 minutes and check Google Cloud Security Command Center for 'Brute Force: SSH' finding."
echo "To verify logs on the target VM, check /var/log/auth.log."
echo "After testing, secure the VM by disabling password authentication and deleting the test user/VM."
