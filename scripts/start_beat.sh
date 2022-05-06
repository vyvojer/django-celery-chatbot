#!/bin/bash

./scripts/wait-for-it.sh $REDIS_HOST:$REDIS_PORT
./scripts/wait-for-it.sh $POSTGRES_HOST:$POSTGRES_PORT

export PYTHONPATH=.

celery --workdir tests -A testproject.celery beat  --loglevel=info
