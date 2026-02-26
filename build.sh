#!/usr/bin/env bash

pip install -r requirements.txt

python manage.py migrate quiz_api --fake
python manage.py migrate

python manage.py collectstatic --noinput