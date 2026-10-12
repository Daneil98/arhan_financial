#!/bin/bash
set -e
echo "--- frontend startup: running migrations ---"
python manage.py migrate --noinput
echo "--- frontend startup: collecting static files ---"
python manage.py collectstatic --noinput -v 1
echo "--- frontend startup: staticfiles contents ---"
ls -R staticfiles | head -30
echo "--- frontend startup: launching gunicorn on PORT=${PORT:-8005} ---"
gunicorn frontend_service.wsgi:application --bind 0.0.0.0:${PORT:-8005}