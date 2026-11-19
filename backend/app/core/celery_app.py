import os
from celery import Celery

# Redis connection
REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)

# Create Celery application
celery_app = Celery(
    "clipforge",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.workers.tasks"]
)

# Worker configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    timezone="UTC",
    enable_utc=True
)
