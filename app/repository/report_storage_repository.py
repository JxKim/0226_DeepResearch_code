"""
封装，报告正文内容存储的方法，可以通过对象存储服务去存储，也可以通过文件系统存储
"""
from uuid import uuid4

from app.schemas.router_schema import ResearchReport
from app.config.config import get_setting
from pathlib import Path
setting = get_setting()
storage_root_dir = setting.storage_root_dir
async def storage_report(report:ResearchReport) -> str:
    """
    依赖agent产生的report，将其存储到具体的 存储后端（OSS或者是文件系统）当中去，然后返回一个uri地址（OSS的地址，或者是文件系统的路径）
    """

    project_id = report.project_id
    storage_id = str(uuid4())
    html = report.html

    report_path = Path(storage_root_dir) / project_id / f"{storage_id}.html"

    report_path.write_text(report.html,encoding="UTF-8")

    return str(report_path)


async def read_report(html_uri) -> str :
    """
    基于一个html_uri，读取正文内容
    """

    html_str = Path(html_uri).read_text(encoding="UTF-8")

    return html_str

