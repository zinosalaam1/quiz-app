#!/usr/bin/env bash

pip install -r requirements.txt

python manage.py makemigrations quiz_api
python manage.py migrate quiz_api 
python manage.py migrate

python manage.py collectstatic --noinput