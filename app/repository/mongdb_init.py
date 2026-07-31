"""
初始化MongoDB的客户端，获取到 当前项目，所对应的mongo 的 数据库 客户端实例
"""
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from app.config.config import get_setting
_database_client: AsyncDatabase | None = None
setting = get_setting()
def get_database_client():

    global _database_client

    if _database_client is None:

        client:AsyncMongoClient  = AsyncMongoClient(
            host=setting.mongodb_uri
        )

        
        _database_client = client[setting.mongodb_database_name]

    return _database_client