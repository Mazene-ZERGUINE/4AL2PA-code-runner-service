#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

echo "Setting environment variables..."
export DJANGO_DEBUG=True
export ENV=dev
export SECRET_KEY='django-insecure-7k1r)gx=f87$_77d&^k6r8kj+q-x)l7605^613o61bhif#uxj5'
export DJANGO_CELERY_BROKER_URL=amqp://localhost
#export S3_BUCKET_NAME=
#export AWS_ACCESS_KEY_ID=
#export AWS_SECRET_ACCESS_KEY=
#export S3_REGION_NAME=

echo "Activating virtual environment..."
source ./venv/bin/activate

echo "Installing requirements..."
pip install -r ./requirements.txt || { echo "Failed to install requirements"; exit 1; }


python manage.py migrate django_celery_results
python manage.py migrate


echo "Starting Django server on port 8080..."
python manage.py runserver 8080 || { echo "Failed to start Django server"; exit 1; }

echo "Django server started successfully"
