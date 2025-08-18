#!/bin/bash

# GCP Organization Access Report Launcher
# This script allows you to run the report from anywhere

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if requirements are installed
if [ ! -d "venv" ] && [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found. Please run: pip install -r requirements.txt"
    exit 1
fi

# Run the report
echo "Running GCP Organization Access Report..."
echo "Working directory: $(pwd)"
echo ""

python3 org_access_report.py

# Keep terminal open if run by double-clicking
if [ "$TERM_PROGRAM" = "Apple_Terminal" ] || [ "$TERM_PROGRAM" = "iTerm.app" ]; then
    echo ""
    echo "Press Enter to close..."
    read
fi 