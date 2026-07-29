"""
定义一个celery app 对象，用来定义task和分发task
"""

from celery import Celery
from app.config.config import get_setting

setting = get_setting()
app = Celery(
    "deep_research",
    broker=setting.celery_redis_uri,
    include=["app.background.research_task"]
)

