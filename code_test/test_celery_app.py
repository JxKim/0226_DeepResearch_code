"""
1、定义celery app，celery，所使用中间件的地址：celery当中，任务生产者，会将任务元数据信息，写到中间件。celery 任务消费者，从中间件读取任务并执行

2、定义celery app当中，包含哪些任务

3、代码中，通过celery app， 来派发任务
"""

from celery import Celery
app = Celery(
    "test_deep_research",
    broker="redis://:infini_rag_flow@localhost:6379/0",
    include=["code_test.test_celery_task"] # 从test.test_celery_task去找任务
)