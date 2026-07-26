"""
NextDrop – Celery Worker Setup
--------------------------------
Initialises the Celery application for asynchronous ML model training tasks.
Uses Redis as the message broker and database as the result backend.
"""

from __future__ import annotations

from celery import Celery

from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "nextdrop_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Auto-discover tasks in the ML and background jobs package
    imports=[
        # "app.ml.training.tasks" will be added here during training phase setup
    ],
)
