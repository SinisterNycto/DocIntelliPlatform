from celery import Celery
from app.core.config import settings
import os

# Initialize Celery pointing to our Redis broker
celery_app = Celery(
    "docintelli_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.ingestion']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
