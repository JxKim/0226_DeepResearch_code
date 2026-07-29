"""
定义整个项目全局的配置，通过Setting 类来定义,
定义一个get_setting方法：返回Setting对象，方法，调用多次，返回的是同一个setting对象
"""
from typing import Optional

from pydantic_settings import BaseSettings



class Setting(BaseSettings):

    api_prefix : str  = "/api/v1"

    # 整体路径：127.0.0.1:8000/api/v1/research-projects/路径
    router_prefix:str = "research-projects"
    celery_redis_uri : str = "redis://:infini_rag_flow@localhost:6379/0"

setting:Optional[Setting] = None

def get_setting() -> Setting:

    global setting

    if setting is None:
        setting = Setting()
        return setting
    else:
        return setting

