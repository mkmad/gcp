# Load Testing and Packet Capture Project

This project includes scripts and configuration for performing load testing on a set of web endpoints using Locust, integrated with packet capturing via TShark to filter and analyze non-200 HTTP response packets.

## Project Structure

- `locustfile.py` - Contains the Locust tasks and user behavior definitions for load testing multiple web endpoints.
- `run_test.sh` - Bash script to run the load test and manage packet capture simultaneously.
- `capture/` - Directory to store all pcap files generated during the tests.
    - `all_traffic.pcap` - Raw capture file containing all traffic during the test.
    - `non_200_responses.pcap` - Filtered capture file containing only packets with non-200 HTTP response codes.
- `requirements.txt` - Specifies the Python packages that need to be installed for running the tests.

## Requirements

To run the tests and packet capture described in this project, you will need:

- Python 3.8 or higher
- TShark (part of the Wireshark suite)

### Python Dependencies

Install the required Python packages using:

```bash
sudo pip install -r requirements.txt
```

### TShark Installation
Install TShark, typically available in your system's package manager. For example, on Ubuntu:

```bash
sudo apt-get install tshark
```

#### Running the Tests
To start the load tests along with packet capturing, execute the bash script:

```bash
sudo ./run_test.sh
```

Ensure you have the necessary permissions to execute the script, particularly for using TShark with root privileges.

#### Analysis
After the test run, the captured packets are filtered based on HTTP response codes, and relevant data is saved in the capture/ directory for further analysis.

Use Wireshark or TShark to open and analyze the non_200_responses.pcap file to investigate packets associated with non-200 responses.

