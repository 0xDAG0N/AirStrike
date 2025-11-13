#!/bin/bash

# Check if script is already running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: AirStrike must be run with root privileges!"
    echo "Please restart with: sudo $0"
    exit 1
fi

echo "Starting AirStrike with root privileges..."

# Make sure the Python environment is preserved when using sudo
# Set up Python path
SCRIPT_DIR=$(dirname "$(readlink -f "$0")") 
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Run with Python available in PATH
python run.py