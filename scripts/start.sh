#!/bin/bash

./scripts/wait-for-it.sh $POSTGRES_HOST:$POSTGRES_PORT

python tests/manage.py migrate
python tests/manage.py runserver 0.0.0.0:8000