web: gunicorn config.wsgi --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120
release: python manage.py migrate --noinput
