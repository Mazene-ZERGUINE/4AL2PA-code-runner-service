#!/bin/bash

echo "initializing python virtual environment"
source /venv/bin/activate
export ENV="production"


echo "installing requirements"
echo " --------------------- "

pip install -r ./requirements.txt || { echo "Failed to install requirements"; exit 1; }

echo "-------------------------"

echo "running celery worker application"
celery -A code_runner_service worker --loglevel=info