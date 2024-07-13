#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

echo "Setting environment variables..."
export ENV=production


echo "Activating virtual environment..."
source ./venv/bin/activate

echo "Installing requirements..."
pip install -r ./requirements.txt || { echo "Failed to install requirements"; exit 1; }

python manage.py makemigrations

python manage.py migrate django_celery_results
python manage.py migrate


echo "Starting Django server on port 8080..."
sudo systemctl start gunicorn
sudo systemctl enable gunicorn


echo "Django server started successfully"
