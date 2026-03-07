"""
Celery Application Configuration
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "reportforge",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

import sys

# Windows-compatible pool configuration
pool_type = 'solo' if sys.platform == 'win32' else 'prefork'

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1,
    # Auto-discover tasks
    imports=('app.tasks.report_tasks',),
    # Use solo pool on Windows (single process, no multiprocessing)
    worker_pool=pool_type,
)

