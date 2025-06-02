# SSH Brute Force Simulation Scripts

This folder contains scripts for simulating SSH brute force attacks, primarily for testing detection capabilities in Google Cloud Platform (GCP) Security Command Center (SCC) and other security monitoring tools.

## Purpose

The main goal of these scripts is to generate realistic SSH brute force activity against a test VM. This helps:

- Test and validate security alerting and detection (e.g., SCC "Brute Force: SSH" findings)
- Train incident response and SOC teams
- Generate logs and artifacts for forensic analysis

## Contents

- **brute_force_ssh.sh**  
  Bash script to simulate multiple failed SSH login attempts (and optionally a successful one) against a target VM.  
  _Note: This script is for use in controlled, test environments only._

## Usage

1. **Prepare the Target VM**
   - Create a test VM in GCP and ensure it is isolated from production systems.
   - Create a temporary test user (e.g., `ubuntu`) with a known password.
   - Enable SSH password authentication on the VM:
     ```bash
     sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
     sudo systemctl restart sshd
     ```
   - Ensure the firewall allows SSH (port 22) only from your source IP.

2. **Configure the Script**
   - Edit `brute_force_ssh.sh` and set:
     - `TARGET_HOST` to your VM's external IP
     - `TARGET_USER` to the test user
     - `PASSWORD_FILE` to a file containing the correct password (this file should be git-ignored)
     - `ATTEMPTS` to the number of failed attempts you want to simulate
   - Ensure dependencies are installed:
     - `sshpass` (for automated SSH attempts)
     - `gcloud` CLI (for firewall checks)

3. **Run the Script**
   ```bash
   ./brute_force_ssh.sh
   ```
   - The script will simulate multiple failed SSH login attempts with random passwords.
   - Optionally, it can attempt a successful login at the end (using the correct password).
   - You will be prompted to confirm before the simulation begins.

4. **After the Test**
   - Wait up to 15 minutes and check GCP SCC for "Brute Force: SSH" findings.
   - Review `/var/log/auth.log` on the target VM for login attempts.
   - Clean up:
     - Delete the test user: `sudo userdel -r <username>`
     - Optionally, disable password authentication again on the VM.
     - Delete the test VM if no longer needed.

## Safety & Security Notes

- **Never run this script against production systems or without explicit permission.**
- Restrict firewall access to only your source IP during testing.
- Use only temporary test users and VMs.
- This script is for educational and security testing purposes only.

## Disclaimer

Use at your own risk. The authors are not responsible for any misuse or damage caused by these scripts. Always follow your organization's security policies and obtain proper authorization before running security tests. 