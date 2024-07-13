#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

echo "Setting environment variables..."
export ENV=production


echo "Checking if virtual environment exists..."
if [ ! -d "./venv" ]; then
    echo "Virtual environment not found, creating one..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source ./venv/bin/activate

echo "Installing requirements..."
pip install -r ./requirements.txt || { echo "Failed to install requirements"; exit 1; }

echo "Starting Celery worker..."
celery -A code_runner_service worker --loglevel=info
