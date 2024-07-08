export DJANGO_DEBUG=True
export ENV=dev
export SECRET_KEY='django-insecure-7k1r)gx=f87$_77d&^k6r8kj+q-x)l7605^613o61bhif#uxj5'
export DJANGO_CELERY_BROKER_URL=amqp://localhost


# run process here

source ./venv/bin/activate

pip install -r ./requirements.txt

python manage.py runserver 8080