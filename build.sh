#!/usr/bin/env bash

pip install -r requirements.txt

python manage.py migrate --fake quiz_api zero
python manage.py migrate
python manage.py collectstatic --noinput