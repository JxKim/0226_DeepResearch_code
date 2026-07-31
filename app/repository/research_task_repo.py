"""
封装了，做研究过程当中，task对象的 增删改查 操作
"""
from pstats import Stats
from uuid import uuid4

from app.schemas.router_schema import InitializeProjectRequest, ResearchBriefAndOutline,ResearchProjectStatusType, TaskStatus, TaskType
from app.repository.mongdb_init import get_database_client
from app.config.config import get_setting
import datetime
setting = get_setting()
collection = get_database_client()[setting.research_task_collection_name]

async def create_task(project_id:str, task_type:str) -> dict:
    """"
    构造一个特定类型的任务，返回任务的dict实例
    初始化任务状态为queued
    """

    task_id = str(uuid4())

    inital_task_dict = {
        "task_id": task_id,
        "project_id": project_id,
        "task_type": task_type,
        "status" :TaskStatus.QUEUED.value,
        "message":"任务已创建",
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now()
    }

    await collection.insert_one(inital_task_dict)

    return inital_task_dict

async def get_task(task_id:str) -> dict | None :
    """
    由task_id，在数据库当中读到task，返回结果
    """

    task:dict |  None = await collection.find_one({"task_id":task_id})


    return task


async def update_status(task_id: str, status: str, message:str) :
    """
    将特定任务（task_id所指定的任务）状态进行变更，变更成status所指定的状态，并附上说明（message）

    """

    await collection.update_one({"task_id":task_id},{"$set":{"status":status,"message":message,"updated_at":datetime.datetime.now()}})