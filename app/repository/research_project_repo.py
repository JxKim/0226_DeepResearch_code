"""
包含了对research_project（研究项目）的读写相关的操作
"""
from uuid import uuid4

from app.schemas.router_schema import InitializeProjectRequest, ResearchBriefAndOutline,ResearchProjectStatusType
from app.repository.mongdb_init import get_database_client
from app.config.config import get_setting
import datetime
setting = get_setting()
collection = get_database_client()[setting.research_project_collection_name]

async def create_project(request:InitializeProjectRequest) -> str:
    """
    接收用户创建项目的请求，返回新的项目的 项目id project_id
    项目状态，初始值是created
    """
    project_id = str(uuid4())
    initial_project_dict = {
        "project_id": project_id,
        "status": ResearchProjectStatusType.CREATED.value,
        # 调用model_dump，将一个pydantic的BasModel，转换成python dict
        "request": request.model_dump(mode="python"),

        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now()

    }

    await collection.insert_one(initial_project_dict)
    return project_id


async def get_project_outline(project_id:str) -> list[dict] | None:
    """
    通过project_id，在数据库当中读取，当前project的大纲(outline):
    返回的结果当中：
    list： 表示的第一个层级的，所有OutlineNode
    dict: 每一个OutlineNode结构
    """

    output_result:dict | None = await collection.find_one({"project_id":project_id},{"outline":1, "_id":0})

    return output_result["outline"] if output_result else None 





async def update_status(project_id, status:ResearchProjectStatusType) :
    """
    将某个项目的状态，进行更新
    """

    await collection.update_one({"project_id":project_id},{"$set":{"status":status.value,"updated_at":datetime.datetime.now()}})


async def get_project_status(project_id:str) -> str | None :
    """
    获取某个项目的状态
    """

    output_result  : dict | None = await collection.find_one({"project_id":project_id},{"status":1, "_id":0})

    return output_result["status"] if output_result else None 


async def insert_brief_and_outline(project_id:str , brief_and_outline:ResearchBriefAndOutline):
    """
    将大纲和任务书，写到project_id所对应的项目当中去
    """

    await collection.update_one({"project_id":project_id},{"$set":{"research_brief":brief_and_outline.research_brief.model_dump(mode="python"),
                                                                   "outline":[outline.model_dump(mode="python") for outline in brief_and_outline.outline],
                                                                    "updated_at":datetime.datetime.now()
                                                                   }})