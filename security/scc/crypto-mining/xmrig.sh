#!/bin/bash

# Duration in seconds (1 hour = 3600 seconds, set to 300 for testing)
TEST_DURATION=300

# Record the start time in UTC with timezone
START_TIME=$(date -u '+%Y-%m-%d %H:%M:%S %Z')

# Temporary file to capture xmrig output
OUTPUT_FILE="xmrig_output.txt"

# Check if xmrig executable exists
if [ ! -x "./xmrig-6.22.2/xmrig" ]; then
    echo "Error: ./xmrig-6.22.2/xmrig not found or not executable" > $OUTPUT_FILE
    exit 1
fi

# Ensure output file is writable
touch $OUTPUT_FILE
if [ ! -w "$OUTPUT_FILE" ]; then
    echo "Error: Cannot write to $OUTPUT_FILE" >&2
    exit 1
fi

# Run xmrig stress test in a new session with tee for output capture
setsid stdbuf -oL -eL ./xmrig-6.22.2/xmrig --stress --verbose --algo=cn-lite/1 --threads=1 2>&1 | tee $OUTPUT_FILE &
XMRIG_PID=$!

# Wait for the specified duration
sleep $TEST_DURATION

# Gently stop the xmrig process group with SIGINT (like Ctrl+C)
kill -INT -- -$XMRIG_PID 2>/dev/null
sleep 3
# Fallback to SIGTERM if still running
kill -TERM -- -$XMRIG_PID 2>/dev/null
sleep 1
# Force kill if still running
kill -KILL -- -$XMRIG_PID 2>/dev/null

# Wait for the process to terminate and get its exit status
wait $XMRIG_PID 2>/dev/null
XMRIG_EXIT_STATUS=$?

# Ensure output file is flushed
sync

# Check for OOM killer evidence
OOM_LOG=$(dmesg | grep -i "killed process.*xmrig" | tail -n 1)

# Record the end time in UTC with timezone
END_TIME=$(date -u '+%Y-%m-%d %H:%M:%S %Z')

# Calculate actual duration
START_EPOCH=$(date -d "$START_TIME" +%s)
END_EPOCH=$(date -d "$END_TIME" +%s)
DURATION_SECONDS=$((END_EPOCH - START_EPOCH))
DURATION=$(printf '%d hour(s), %d minute(s), %d second(s)' $((DURATION_SECONDS/3600)) $((DURATION_SECONDS%3600/60)) $((DURATION_SECONDS%60)))

# Generate the report
REPORT_FILE="xmrig_stress_test_report.txt"
{
    echo "xmrig Stress Test Report"
    echo "-----------------------"
    echo "Start Time: $START_TIME"
    echo "End Time: $END_TIME"
    echo "Duration: $DURATION"
    echo "xmrig Exit Status: $XMRIG_EXIT_STATUS"
    if [ -n "$OOM_LOG" ]; then
        echo "OOM Killer Log: $OOM_LOG"
    fi  
    echo -e "\nStress Test Output:"
    echo "-------------------"
    if [ -s "$OUTPUT_FILE" ]; then
        cat $OUTPUT_FILE
    else
        echo "No output captured. Debugging info:"
        if [ -f "$OUTPUT_FILE" ]; then
            echo "File $OUTPUT_FILE exists, size: $(stat -c %s $OUTPUT_FILE) bytes"
            echo "Permissions: $(ls -l $OUTPUT_FILE)"
        else
            echo "File $OUTPUT_FILE does not exist."
        fi  
    fi  
} > $REPORT_FILE

# Clean up temporary output file
rm -f $OUTPUT_FILE

echo "Stress test completed. Report generated at $REPORT_FILE"