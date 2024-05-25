#!/resources/bash

# Activate the virtual environment
source venv/bin/activate

# Build Docker image
docker build -t code_runner:latest .

# Run RabbitMQ server in the background
docker run -d --hostname my-rabbit --name some-rabbit -p 5672:5672 -p 15672:15672 rabbitmq:3-management &


# Run Celery worker in the background
celery -A code_runner_service worker --loglevel=info &

# Run Django application server in the foreground (this will keep the terminal busy with this task)
python manage.py runserver
