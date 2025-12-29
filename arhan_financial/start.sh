#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting Deployment Script..."

# 1. Run Database Migrations
# Since you have no terminal access on Render Free Tier, 
# this ensures the DB is updated automatically every time you deploy.
echo "🗄️ Running Migrations..."
python manage.py migrate --noinput

# 2. Collect Static Files
# Essential because Render uses WhiteNoise to serve CSS/JS.
echo "🎨 Collecting Static Files..."
python manage.py collectstatic --noinput

# 3. Start Celery in the background
# The '&' symbol puts it in the background so the script continues.
echo "👷 Starting Celery Worker..."
celery -A arhan_financial worker --loglevel=info &

# 4. Start Gunicorn in the foreground
# This keeps the container running.
echo "🦄 Starting Gunicorn..."
gunicorn arhan_financial.wsgi:application --bind 0.0.0.0:$PORT