"""
包含了对research_project（研究项目）的读写相关的操作
"""
from app.schemas.router_schema import InitializeProjectRequest,ResearchProjectStatusType

async def create_project(request:InitializeProjectRequest) -> str:
    """
    接收用户创建项目的请求，返回新的项目的 项目id project_id
    项目状态，初始值是created
    """

    pass 


async def get_project_outline(project_id:str) -> list[dict]:
    """
    通过project_id，在数据库当中读取，当前project的大纲(outline):
    返回的结果当中：
    list： 表示的第一个层级的，所有OutlineNode
    dict: 每一个OutlineNode结构
    """


async def update_status(project_id, status:ResearchProjectStatusType) :
    """
    将某个项目的状态，进行更新
    """


async def get_project_status(project_id:str) -> str:
    """
    获取某个项目的状态
    """


async def get_latest_report(project_id:str) -> dict:
    """
    读取某个项目，最新的一次报告。
    系统可以设计成：
        单个项目，可以做多次研究，存储多次结果，用户可以前端比较多次结果，最终去判断，需要哪一个版本

    """