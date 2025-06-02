# Crypto Mining Stress Test Scripts

This folder contains scripts and resources for simulating and detecting crypto mining activity, specifically for security testing and Security Command Center (SCC) use cases in Google Cloud Platform (GCP) environments.

## Purpose

The primary goal of these scripts is to simulate crypto mining workloads (using the popular `xmrig` miner in stress test mode) on a system. This can help:

- Test detection capabilities of security monitoring tools (e.g., GCP SCC, SIEMs, EDRs).
- Evaluate system behavior and resource limits under mining-like CPU stress.
- Generate logs and artifacts for incident response and forensic analysis training.

## Contents

- **xmrig.sh**  
  Bash script to run `xmrig` in stress test mode for a configurable duration, capture its output, and generate a detailed report.  
  _Note: The actual `xmrig` binary is not included and must be downloaded separately._

- **xmrig-6.22.2/**  
  (Expected directory for the `xmrig` executable. Not included in this repo.)

## Usage

1. **Download xmrig**  
   Download the `xmrig` binary (version 6.22.2 or compatible) and place it in a subdirectory named `xmrig-6.22.2` within this folder.  
   Example:
   ```bash
   mkdir xmrig-6.22.2
   cd xmrig-6.22.2
   wget https://github.com/xmrig/xmrig/releases/download/v6.22.2/xmrig-6.22.2-linux-x64.tar.gz
   tar -xzf xmrig-6.22.2-linux-x64.tar.gz
   # Ensure xmrig is executable
   chmod +x xmrig
   cd ..
   ```

2. **Run the Stress Test Script**  
   Execute the script to start the mining stress test:
   ```bash
   ./xmrig.sh --stress --verbose --algo=cn-lite/1 --threads=1
   ```
   - The script runs `xmrig` in stress mode for a default of 300 seconds (5 minutes). You can adjust the `TEST_DURATION` variable in the script for longer or shorter tests.
   - Output and a summary report will be generated in the current directory.

3. **Review the Report**  
   After completion, check `xmrig_stress_test_report.txt` for:
   - Start/end times and duration
   - xmrig exit status
   - Any OOM (Out Of Memory) killer events
   - Full output from the xmrig run

4. **Cleanup**  
   The script automatically removes temporary output files after generating the report.

## Notes

- **Permissions:** Ensure the script and xmrig binary are executable (`chmod +x xmrig.sh xmrig-6.22.2/xmrig`).
- **System Impact:** This script will consume CPU resources. Do not run on production systems.
- **Security:** Running mining software may trigger security alerts. Use only in controlled, test environments.
- **Dependencies:** The script uses standard Linux utilities (`date`, `setsid`, `stdbuf`, `tee`, `kill`, `dmesg`, etc.).

## Disclaimer

This script is for educational and security testing purposes only. Do not use for unauthorized mining or on systems you do not own or have explicit permission to test. 