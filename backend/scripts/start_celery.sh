#!/bin/bash

# Start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info &

# Start Celery beat (scheduler)
celery -A app.tasks.celery_app beat --loglevel=info
