#!/bin/bash

./scripts/wait-for-it.sh $REDIS_HOST:$REDIS_PORT
./scripts/wait-for-it.sh $POSTGRES_HOST:$POSTGRES_PORT

export PYTHONPATH=.

: ${WORKER_CONCURRENCY:=2}
celery --workdir tests -A testproject.celery worker -E --loglevel=info --concurrency=$WORKER_CONCURRENCY -n worker
