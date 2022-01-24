#!/bin/bash

./scripts/wait-for-it.sh app:8000
cd ./tests
python manage.py test