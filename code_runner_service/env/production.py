import os
DEBUG = True

# production database connection configurations
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv('CODE_RUNNER_DATABASE_NAME'),
        "USER": os.getenv('CODE_RUNNER_DATABASE_USERNAME'),
        "PASSWORD": os.getenv('CODE_RUNNER_DATABASE_PASSWORD'),
        "HOST": os.getenv('CODE_RUNNER_DATABASE_ENDPOINT'),
        "PORT": os.getenv('CODE_RUNNER_DATABASE_PORT', '5432'),
    }
}

# allowed hosts in production replace with nestJS api instance
# ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS').split(',')

# celery production configurations replace with celery broker url
CELERY_BROKER_URL = 'amqps://esgithub:4AL2-PA-2024@b-083e498a-240b-4d98-b585-6fb241dcc8c8.mq.eu-west-3.amazonaws.com:5671'
CELERY_RESULT_BACKEND = 'django-db'


# production s3 bucket configurations
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
S3_REGION_NAME = os.getenv('S3_REGION_NAME')