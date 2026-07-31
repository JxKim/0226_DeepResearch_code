"""
对于一个project，每生成一个报告的版本，会将该版本，所对应的版本信息（版本所对应的uri地址，版本号、创建时间等元数据信息），写到数据库当中去
该repo封装了 读写操作
"""

from uuid import uuid4
import datetime
from app.repository import report_storage_repository
from app.schemas.router_schema import ResearchReport
from app.config.config import get_setting
from app.repository.mongdb_init import get_database_client
setting = get_setting()

# 得到，report_version collection 实例对象，后面通过该对象，来完成数据的增删改查
collection = get_database_client()[setting.report_version_collection_name]
async def save_version(report:ResearchReport, report_uri: str ):
    """
    对于一个project，每生成一个报告的版本，会将该版本，所对应的版本信息（版本所对应的uri地址，版本号、创建时间等元数据信息），写到数据库当中去
    """

    report_id = str(uuid4())
    project_id = report.project_id

    title = report.title

    report_uri = report_uri

    sources = report.sources

    # 在report_version集合当中，找到所有project_id为传入的report的project_id的所有报告，按照version进行倒序排序，找到最大的版本所对应的报告

    result = await collection.find_one({"project_id":project_id},sorted = [{"version":-1}])

    current_report_version = result["version"] + 1 if result else 1

    report_dict = {
        "report_id": report_id,
        "project_id": project_id,
        "version": current_report_version,
        "title":title,
        "html_uri": report_uri,
        "sources": [source.model_dump(mode="python") for source in sources ],
        "created_at": datetime.datetime.now()
    }

    await collection.insert_one(report_dict)






async def get_latest_report(project_id:str) -> dict:

    """
    
    基于project_id，找到最新的版本的元数据信息，依赖，report_storage_repo，基于uri读取到，然后封装成一个完整的report dict对象，返回出去
    """

    result = await collection.find_one({"project_id":project_id},sorted = [{"version":-1}])

    # 调用report_storage_repo，读取到html，写到result里面去

    html_str:str = await report_storage_repository.read_report(result["html_uri"])

    result["html"]=html_str

    return result