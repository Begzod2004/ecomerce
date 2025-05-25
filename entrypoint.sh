#!/bin/bash

set -e

# Set Docker container environment variable
export DOCKER_CONTAINER=true

# Install any missing dependencies
pip install -r requirements.txt --quiet

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! pg_isready -h db -p 5432 -U postgres; do
    sleep 1
done
echo "PostgreSQL started"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 