#!/bin/sh

./manage.py collectstatic --noinput
./manage.py migrate --noinput
exec /usr/local/bin/gunicorn --workers 1 --threads 8 boran.wsgi
