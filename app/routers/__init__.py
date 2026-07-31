"""
定义项目中所有的接口的路由函数
"""

from typing import Optional

from app.config.config import get_setting
from fastapi import APIRouter, HTTPException
from app.schemas.router_schema import (InitializeProjectRequest, InitializeProjectResponse,GetOutlineResponse,
ConfirmOrReviseOutlineRequest,ConfirmOrReviseOutlineResponse,GenerateReportRequest,GenerateReportResponse,
GetTaskStatusResponse,GetLatestReportResponse,TaskType,ResearchProjectStatusType,OutlineNode,ActionType)
from  app.repository import research_project_repo, research_task_repo,report_version_repository
from app.background.research_task import schedule_task
from datetime import datetime


setting = get_setting()
router = APIRouter(prefix=setting.router_prefix)



@router.post("/", response_model=InitializeProjectResponse)
async def initialize_project(request:InitializeProjectRequest):
    """
    用户输入研究主题和设定，返回project_id和大纲生成的task_id
    入参：
        {
        "topic": "研究具身智能行业未来三年的机会",
        "research_goal": "判断公司是否需要关注该行业",
        "target_audience": "公司战略团队",
        "region_scope": "china",
        "time_scope": {
            "type": "recent_years",
            "years": 3
        }
        }
    出参：
        {
        "project_id": "项目编号",
        "initial_task_id": "任务编号",
        "initial_task_type": "generate_research_brief",
        "topic": "研究具身智能行业未来三年的机会",
        "status": "brief_generating",
        "created_at": "2026-06-05T08:00:00Z"
        }

    需要做的事情：
        1、调用repository的包，在数据库当中创建一个项目
        2、构建一个后台任务：生成大纲的后台任务
        3、将后台任务的id: task_id 返回给前端
    """
    # 1、调用repository的包，在数据库当中创建一个项目
    project_id = await research_project_repo.create_project(request)

    # 2、构建一个后台任务：生成大纲的后台任务
    # 2.1、在数据库当中，创建一个task对象，指定task_type，初始化task的 status为queued
    task =  await research_task_repo.create_task(project_id,task_type = TaskType.GENERATE_RESEARCH_BRIEF)
    # 2.2、放到后台任务当中执行

    schedule_task(task)

    # 3、将相关数据，封装成response对象，输出
    return InitializeProjectResponse(
        project_id=project_id,
        initial_task_id=task['task_id'],
        initial_task_type=TaskType.GENERATE_RESEARCH_BRIEF,
        topic=request.topic,
        status=ResearchProjectStatusType.BRIEF_GENERATING,
        created_at= datetime.now()
    )



    


# GET /api/v1/research-projects/{project_id}/outline

@router.get("/{project_id}/outline",response_model=GetOutlineResponse)
async def get_outline(project_id: str):
    """
    前端传入project_id，
    输出大纲草案
    """
    # 1、通过research_project_repo 来实现大纲读取
    outline_list:list[dict] | None = await research_project_repo.get_project_outline(project_id)

    # 2、将outline，从list[list] 转换成 list[OutlineNode]

    outline_node_list:list[OutlineNode] = [OutlineNode.model_validate(outline)  for outline in outline_list] if outline_list else []

    # 3、封装输出对象
    return GetOutlineResponse(
        project_id=project_id,
        status=ResearchProjectStatusType.OUTLINE_READY,
        outline= outline_node_list
    )


# PUT /api/v1/research-projects/{project_id}/outline

@router.put("/{project_id}/outline",response_model=ConfirmOrReviseOutlineResponse)
async def confirm_or_revise_outline(project_id:str,data : ConfirmOrReviseOutlineRequest):
    """
    用户确认或者是修改大纲
    """

    # 1、从用户data当中，去获取到action，判断action是什么，是confirm，还是revise

    action = data.action

    if action == ActionType.CONFIRM:
        # 如果action = confirm的话，
        # 1、更新数据库当中，项目的状态，由outline_ready转换成outline_confirmed
        await research_project_repo.update_status(project_id, ResearchProjectStatusType.OUTLINE_CONFIRMED)
        # 2、输出结果，此时revision_task_id为None就可以了
        return ConfirmOrReviseOutlineResponse(
            project_id=project_id,
            revision_task_id=None,
            status = ResearchProjectStatusType.OUTLINE_CONFIRMED
        )

    else:

        # 1、更新数据库当中，项目的状态, 由outline_ready转换成 outline_revising
        await research_project_repo.update_status(project_id, ResearchProjectStatusType.OUTLINE_REVISING)

        # 2、新建一个task: 修订大纲的task
        task = await research_task_repo.create_task(project_id=project_id, task_type=TaskType.REVISE_OUTLINE)

        # 3、把task交由background调度执行
        schedule_task(task, data.revision_instruction)

        # 4、把task_id 返回给前端，就可以了
        return ConfirmOrReviseOutlineResponse(
            project_id=project_id,
            revision_task_id=task["task"],
            status = ResearchProjectStatusType.OUTLINE_REVISING
        )


# POST /api/v1/research-projects/{project_id}/report-tasks

@router.post("/{project_id}/report-tasks",response_model=GenerateReportResponse)
async def generate_report(project_id:str,data:GenerateReportRequest):
    """
    用户发起，生成报告的请求,接口启动异步任务，返回task_id
    """
    # 0、标准状态机设计，会在前面，再额外添加一个状态判断，以当前例子来讲，就是会判断project的状态，是否为OUTLINE_CONFIRMED，
        # 如果是的话，才能够进行状态流转，否则，不能够进行状态流转
    project_status = await research_project_repo.get_project_status(project_id)

    if not project_status == ResearchProjectStatusType.OUTLINE_CONFIRMED.value:
        raise HTTPException(status_code=400,detail="当前项目，大纲未确认，无法进行报告生成")

    # 1、创建一个task: task_type: generate_report
    task = await research_task_repo.create_task(project_id=project_id, task_type=TaskType.GENERATE_REPORT)

    # 2、将项目状态，调整为RESEARCH_RUNNING
    await research_project_repo.update_status(project_id=project_id, status=ResearchProjectStatusType.RESEARCH_RUNNING)
    # 3、schedule_task: 做调度
    schedule_task(task,data.user_instruction)
    # 4、返回task_id
    return GenerateReportResponse(
        task_id=task["task_id"],
        project_id=project_id,
        task_type=TaskType.GENERATE_REPORT,
        status=ResearchProjectStatusType.RESEARCH_RUNNING
    )


# GET /api/v1/research-projects/tasks/{task_id}

@router.get("/tasks/{task_id}",response_model=GetTaskStatusResponse)
async def get_task_status(task_id:str):
    """
    通用的，获取异步任务状态的接口，前端可轮询调用，判断任务是否完成
    """

    task:Optional[dict] = await research_task_repo.get_task(task_id)

    if task == None:
        raise HTTPException(status_code=404,detail="当前异步任务，未在数据库当中找到")

    return GetTaskStatusResponse(
        task_id=task_id,
        project_id=task["project_id"],
        task_type=task["task_type"],
        status = task["status"],
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        message = task["message"]
    )



# GET /api/v1/research-projects/{project_id}/reports/latest


@router.get("/{project_id}/reports/latest",response_model=GetLatestReportResponse)
async def get_latest_report(project_id : str):
    """
    获取当前项目，最新的报告
    """

    # 1、从数据库，读取project_id所对应的最新报告

    report = await  report_version_repository.get_latest_report(project_id)

    return GetLatestReportResponse(
        project_id = project_id,
        report_id = report["report"],
        version = report["version"],
        title= report["title"],
        html= report["html"],
        sources= report["sources"],
        created_at= report["created_at"]
    )
