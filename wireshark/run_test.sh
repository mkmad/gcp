#!/bin/bash

trap 'echo "Interrupted!"; sudo kill $TSHARK_PID; exit 1' INT

# Directory and filenames for TShark capture
CAPTURE_DIR="capture"
RAW_PCAP_FILE="${CAPTURE_DIR}/all_traffic.pcap"
FILTERED_PCAP_FILE="${CAPTURE_DIR}/non_200_responses.pcap"

# Ensure the capture directory exists
mkdir -p $CAPTURE_DIR
sudo chown $(whoami) $CAPTURE_DIR
chmod 755 $CAPTURE_DIR

# Start packet capture with TShark
echo "Starting packet capture..."
sudo tshark -i any -w $RAW_PCAP_FILE -f "tcp port 3000 or host brg2.satisfi4.com" & TSHARK_PID=$!
echo "TShark PID: $TSHARK_PID"

# Start Locust in headless mode for a specified run time
echo "Starting Locust tests..."
locust -f locustfile.py --headless --users 3000 --spawn-rate 100 --run-time 10m

# Wait for Locust to finish
wait

# Stop packet capture when Locust tests finish
echo "Stopping packet capture..."
if kill -0 $TSHARK_PID > /dev/null 2>&1; then
    sudo kill $TSHARK_PID
    wait $TSHARK_PID  # Wait for TShark to fully terminate
fi

# Apply filter to the captured packets to isolate non-200 HTTP responses
echo "Filtering for non-200 HTTP responses..."
sudo tshark -r $RAW_PCAP_FILE -Y "http.response.code != 200" -w $FILTERED_PCAP_FILE

echo "Locust tests and packet capture completed."