#!/bin/sh

./manage.py collectstatic --noinput
./manage.py migrate --noinput
exec /usr/local/bin/gunicorn -w 8 boran.wsgi
