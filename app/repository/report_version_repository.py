"""
对于一个project，每生成一个报告的版本，会将该版本，所对应的版本信息（版本所对应的uri地址，版本号、创建时间等元数据信息），写到数据库当中去
该repo封装了 读写操作
"""

from app.schemas.router_schema import ResearchReport


async def save_version(report:ResearchReport, report_uri: str ):
    """
    对于一个project，每生成一个报告的版本，会将该版本，所对应的版本信息（版本所对应的uri地址，版本号、创建时间等元数据信息），写到数据库当中去
    """


async def get_latest_report(project_id:str) -> dict:

    """
    
    基于project_id，找到最新的版本的元数据信息，依赖，report_storage_repo，基于uri读取到，然后封装成一个完整的report dict对象，返回出去
    """