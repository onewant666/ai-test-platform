"""Celery 异步任务队列配置"""

from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ai_test_platform",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.executor"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)
