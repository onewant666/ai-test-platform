"""Celery Worker 入口"""

from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ai_test_platform",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["celery_app.tasks.execution"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,       # 单个任务最多 10 分钟
    task_soft_time_limit=540,  # 软超时 9 分钟
    worker_max_tasks_per_child=50,
)
