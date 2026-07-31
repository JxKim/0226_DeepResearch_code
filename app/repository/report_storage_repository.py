"""
封装，报告正文内容存储的方法
"""
from app.schemas.router_schema import ResearchReport

async def storage_report(report:ResearchReport) -> str:
    """
    依赖agent产生的report，将其存储到具体的 存储后端（OSS或者是文件系统）当中去，然后返回一个uri地址（OSS的地址，或者是文件系统的路径）
    """