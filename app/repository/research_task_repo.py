"""
封装了，做研究过程当中，task对象的 增删改查 操作
"""

async def create_task(project_id:str, task_type:str) -> dict:
    """"
    构造一个特定类型的任务，返回任务的dict实例
    初始化任务状态为queued
    """

    pass

async def get_task(task_id:str) -> dict :
    """
    由task_id，在数据库当中读到task，返回结果
    """