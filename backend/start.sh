#!/bin/bash

# Start the local Redis server in the background
redis-server --daemonize yes

# Wait a second for Redis to boot
sleep 1

# Start the Celery worker in the background
celery -A app.tasks worker --loglevel=info --concurrency=1 &

# Start the FastAPI web server in the foreground on HuggingFace's required port (7860)
uvicorn app.main:app --host 0.0.0.0 --port 7860
