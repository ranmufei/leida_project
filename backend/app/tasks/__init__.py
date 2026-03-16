"""
Celery任务模块
"""
from app.tasks.celery_app import celery_app
from app.tasks import download_tasks

__all__ = [
    "celery_app",
    "download_tasks"
]
