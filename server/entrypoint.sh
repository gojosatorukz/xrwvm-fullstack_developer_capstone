#!/bin/sh
set -eu
if [ -z "${DJANGO_SECRET_KEY:-}" ]; then
    DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
    export DJANGO_SECRET_KEY
fi
python manage.py migrate --noinput
python manage.py shell -c 'from djangoapp.populate import initiate; initiate()'
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 djangoproj.wsgi:application
