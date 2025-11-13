#!/bin/bash

# Ensure log directory exists
mkdir -p logs

# Kill any existing instances
pkill -f "python run.py" || true

# Set environment variables
export GEVENT_SUPPORT=True
export PYTHONUNBUFFERED=1

# Clear terminal
clear

# Run the application with sudo, redirecting error output to a log file
sudo python run.py 2>logs/errors.log

# If the app exits, show a message
echo "Application exited. Check logs/errors.log for any issues." 