import asyncio
import re
import stat
from app.celery_app import app
from app.repository import report_storage_repository, report_version_repository, research_project_repo
from app.schemas.router_schema import ResearchProjectStatusType, TaskStatus, TaskType,ResearchBriefAndOutline, ResearchSection,ResearchReport
import  app.repository.research_task_repo as task_repo
from app.agents import research_agent

def schedule_task(task:dict, *args):
    """
    调度任务执行，这个方法是一个非阻塞的调用。也就是说，task_id传过来只能够，该方法所做的事情，就是将任务投递到后台任务中执行就可以了
    task_id：当前任务的任务id
    *args: 当前任务，其他的参数

    当任务具体执行时，状态才改成running，执行成功，改成succeed,失败，改成failed
    """
    task_type = task["task_type"]
    task_id = task["task_id"]
    project_id = task["project_id"]

    if task_type == TaskType.GENERATE_RESEARCH_BRIEF.value:
        # 所谓调度任务，就是将 任务，写到 celery 的中间件 redis当中，通过send_task来写
        app.send_task("generate_brief_and_outline", args=(project_id,task_id))

    elif task_type  == TaskType.REVISE_OUTLINE.value:

        revision_instruction = args[0]
        app.send_task("revise_outline",args = (project_id, revision_instruction,task_id))


    elif task_type == TaskType.GENERATE_REPORT.value:

        user_instruction =  args[0]
        app.send_task("generate_report", args=(project_id, user_instruction,task_id))

    else:
        raise Exception(f"当前任务类型{task_type} 尚未定义")


_work_loop = None

def _get_worker_event_loop():
    """
    创建一个事件循环对象，
    后面通过该对象的run_until_complete() 方法，来执行协程。

    在Python当中，通过async def 所定义的，是一个异步方法,
    调用该异步方法(不带await)，得到的就是一个协程对象。

    所有的协程对象，都必须要在事件循环（event loop）去执行

    事件循环的作用：找到可以执行的协程，并执行它，直到这个协程，有新的异步操作了，event loop就会把该协程，重新放到事件循环，再先去执行其他的协程，直到所有的协程，全部都执行完毕

    该方法，在celery 任务消费者（也就是我们启动worker 进程）当中，创建一个全局的event_loop，供协程运行
    """

    global _work_loop

    if _work_loop is None:
        _work_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_work_loop)

    return _work_loop
    
def _run_async(coroutine):
    """
    将实际任务的协程对象，传递给_run_async方法，其会通过event_loop来执行 该协程，从而就能够实现在，在同步方法里面，去调用异步方法
    """

    loop = _get_worker_event_loop()

    loop.run_until_complete(coroutine)

# celery的app当中所包含的任务一： 项目初始化时，生成项目任务书的大纲的任务
@app.task(name = "generate_brief_and_outline")
def generate_brief_and_outline(project_id: str,task_id:str):
    """
    生成项目任务书的大纲的任务，接收的project_id
    """

    _run_async(_generate_brief_and_outline(project_id,task_id))

    


@app.task(name = "revise_outline")
def revise_outline(project_id:str, revision_instruction:str,task_id:str):
    """
    修订大纲的任务：
        project_id: 项目id
        revision_instruction: 用户传入的，大纲修订的意见
    """

    _run_async(_revise_outline(project_id=project_id,revision_instruction=revision_instruction,task_id=task_id))


@app.task(name = "generate_report")
def generate_report(project_id:str, user_instruction:str,task_id:str):
    """
    生成报告的任务：
        project_id: 项目id
        user_instruction：用户传入的，生成报告时的要求
    """

    _run_async(_generate_report(project_id, user_instruction,task_id))



async def _generate_brief_and_outline(project_id:str,task_id:str):
    """
    生成任务书和大纲的实际执行的任务：
    1、将任务（task）的状态，从queued变成running的状态
    2、调整项目的状态：从created变成 brief_generating的状态

    3、依赖app/agents模块，实现 大纲生成的过程
        调用app/agents/research_agent.py 模块，获取一个research_agent的实例，调用该实例的generate_brief_and_outline方法，生成大纲
        通过该方法，能够获取到大纲和任务书

    4、调用research_project_repo，将大纲和任务书，保存到数据库当中去

    5、调整项目的状态：从brief_generating的状态变成outline_ready

    6、将任务（task）状态，从running，改成succeeded
    """

    try:
        # 1、将任务（task）的状态，从queued变成running的状态
        await task_repo.update_status(task_id, status = TaskStatus.RUNNING,message = "正在执行 大纲和任务书 生成 任务")

        # 2、调整项目的状态：从created变成 brief_generating的状态
        await research_project_repo.update_status(project_id,status=ResearchProjectStatusType.BRIEF_GENERATING)

        # 3、依赖app/agents模块，实现 大纲生成的过程
        agent: research_agent.ResearchAgent  = research_agent.get_agent()

        brief_and_outline: ResearchBriefAndOutline = await agent.generate_brief_and_outline(project_id)

        # 4、调用research_project_repo，将大纲和任务书，保存到数据库当中去

        await research_project_repo.insert_brief_and_outline(project_id, brief_and_outline)

        # 5、调整项目的状态：从brief_generating的状态变成outline_ready

        await research_project_repo.update_status(project_id,status=ResearchProjectStatusType.OUTLINE_READY)

        # 6、将任务（task）状态，从running，改成succeeded


        await task_repo.update_status(task_id, status = TaskStatus.SUCCEEDED,message = "大纲和任务书，已生成完成")
    except Exception as e:

        await task_repo.update_status(task_id, status = TaskStatus.FAILED,message = f"生成任务书的过程，发生异常，异常信息：{str(e)}")

        raise e





async def _revise_outline(project_id:str,revision_instruction:str,task_id:str):
    """
    修订任务书和大纲的实际执行的任务

    1、把这个异步任务（task）,从quened变成running
    2、调整项目状态：从outline_ready调整成outline_revising
    3、依赖app/agents模块，实现 修订大纲过程
        获取research_agent实例，基于该实例，来实现修订
    
    4、调用research_project_repo，对第3步返回的大纲，进行保存，保存到数据库当中去

    5、调用项目状态：从outline_revising调整成 outline_ready

    6、调整任务状态: 从running，调整成succeeded
    """

    try:
        # 1、把这个异步任务（task）,从quened变成running
        await task_repo.update_status(task_id,status=TaskStatus.RUNNING, message="正在执行 修订大纲的任务")

        # 2、调整项目状态：从outline_ready调整成outline_revising
        await research_project_repo.update_status(project_id=project_id, status=ResearchProjectStatusType.OUTLINE_REVISING)

        # 3、依赖app/agents模块，实现 修订大纲过程
        #         获取research_agent实例，基于该实例，来实现修订
        agent = research_agent.get_agent()

        new_brief_and_outline: ResearchBriefAndOutline = await agent.revise_outline(project_id, revision_instruction)


        # 4、调用research_project_repo，对第3步返回的大纲，进行保存，保存到数据库当中去
        await research_project_repo.insert_brief_and_outline(project_id, new_brief_and_outline)

        # 5、调用项目状态：从outline_revising调整成 outline_ready
        await research_project_repo.update_status(project_id=project_id, status=ResearchProjectStatusType.OUTLINE_READY)

        # 6、调整任务状态: 从running，调整成succeeded
        await task_repo.update_status(task_id,status=TaskStatus.SUCCEEDED, message="修订大纲的任务 已成功完成")


    except Exception as e:

        await task_repo.update_status(task_id, status = TaskStatus.FAILED,message = f"生成任务书的过程，发生异常，异常信息：{str(e)}")

        raise e        


async def _generate_report(project_id:str, user_instruction:str,task_id:str):
    """
    生成报告的实际执行的任务

    1、把这个异步任务（task）,从quened变成running
    2、调整项目状态：从outline_confirmed调整成research_running
    3、依赖app/agents模块，实现 报告生成的过程
            3.1 获取research_agent实例，
            3.2 调用该实例的第一个方法：generate_sections，逐章节生成章节内容，获取到各个section的具体内容

            3.3 调用该实例的第二个方法：generate_report, 依赖各个section的具体内容，渲染，生成最终的报告 report


    4、调用 report_storag_repository, 将report 存储起来，

        再调用 report_version_repository， 将报告的元数据信息，写到数据库当中去

    5、调整项目状态：从research_running调整成report_ready

    6、把这个异步任务（task）,从running变成succeeded
    """
    try:
        # 1、把这个异步任务（task）,从quened变成running
        await task_repo.update_status(task_id,status=TaskStatus.RUNNING, message="正在执行 修订大纲的任务")

        # 2、调整项目状态：从outline_ready调整成outline_revising
        await research_project_repo.update_status(project_id=project_id, status=ResearchProjectStatusType.RESEARCH_RUNNING)

        project = await research_project_repo.get_project(project_id)
        # 3、依赖app/agents模块，实现 报告生成的过程
        #         3.1 获取research_agent实例，
        #         3.2 调用该实例的第一个方法：generate_sections，逐章节生成章节内容，获取到各个section的具体内容

        #         3.3 调用该实例的第二个方法：generate_report, 依赖各个section的具体内容，渲染，生成最终的报告 report


        agent: research_agent.ResearchAgent  = research_agent.get_agent()

        sections:list[ResearchSection] = await agent.generate_sections(project_id, user_instruction)

        report: ResearchReport = await agent.generate_report(sections,topic=project["topic"])

        # 4、调用 report_storage_repository, 将report 存储起来，
            # 实际生产环境下：对象存储服务，OSS MinIO，在当前项目，要想简单实现，可以将html存储到文件系统当中去。
            # 存储后，会得到一个存储的路径，html_uri，数据库当中存储的，是这个uri地址，后面读取时，先基于数据库，读取到uri地址，然后再读取具体对象内容

        #     再调用 report_version_repository， 将报告的元数据信息，写到数据库当中去>

        report_uri  = await report_storage_repository.storage_report(report=report)

        await report_version_repository.save_version(report, report_uri)


        # 5、调整项目状态：从research_running调整成report_ready

        await research_project_repo.update_status(project_id=project_id, status=ResearchProjectStatusType.REPORT_READY)
        # 6、把这个异步任务（task）,从running变成succeeded

        await task_repo.update_status(task_id,status=TaskStatus.SUCCEEDED, message="报告已生成完成")

    except Exception as e:

        await task_repo.update_status(task_id, status = TaskStatus.FAILED,message = f"报告生成的过程，发生异常，异常信息：{str(e)}")

        raise e   





