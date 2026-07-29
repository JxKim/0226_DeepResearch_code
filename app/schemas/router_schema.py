"""
定义 接口的出入参的 结构，通过pydantic的BaseModel来定义
"""

from pydantic import BaseModel
from pydantic import Field
from enum import StrEnum
from datetime import datetime
from typing import List, Optional

class RegionScope(StrEnum):

    CHINA = "china"
    OVERSEAS = "overseas"
    GLOBAL = "global"

class TimeScope(StrEnum):

    UNLIMITED = "unlimited"
    RECENT_YEARS = "recent_years"

class TaskType(StrEnum):

    GENERATE_RESEARCH_BRIEF="generate_research_brief"
    GENERATE_REPORT = "generate_report"
    REVISE_OUTLINE = "revise_outline"

class ResearchProjectStatusType(StrEnum):
    # 接近于 状态机 
    CREATED = "created"
    BRIEF_GENERATING = "brief_generating"

    OUTLINE_READY= "outline_ready"

    OUTLINE_REVISING = "outline_revising"

    OUTLINE_CONFIRMED = "outline_confirmed"

    RESEARCH_RUNNING = "research_running"

    REPORT_READY = "report_ready"

class InitializeProjectRequest(BaseModel):

    topic: str = Field(description="用户输入的研究主题")
    research_goal : str = Field(description="用户所需要达到的研究目标")

    target_audience : str = Field(description="目标受众")

    region_scope: RegionScope

    time_scope : TimeScope

class InitializeProjectResponse(BaseModel):

    project_id: str 
    initial_task_id: str
    initial_task_type: TaskType

    topic: str

    status: ResearchProjectStatusType = Field(description="项目状态")

    created_at: datetime

class OutlineNode(BaseModel):

    node_id: str
    title:str
    question:str
    description:str
    children : List['OutlineNode']

class TaskStatus(StrEnum):

    QUEUED="queued" # 排队状态，接口创建了任务，将其推给了后台celery
    RUNNING="running" # 后台celery，调度到了该任务，并执行时的状态
    SUCCEEDED="succeeded" # 当前任务，正常执行完成
    FAILED="failed" # 当前任务，执行失败



class GetOutlineResponse(BaseModel):

    project_id: str 
    status:ResearchProjectStatusType = Field(description="项目状态")

    outline: List[OutlineNode]

class ActionType(StrEnum):

    CONFIRM = "confirm"
    REVISE = "revise"

class ConfirmOrReviseOutlineRequest(BaseModel):

    action: ActionType 
    revision_instruction: Optional[str]

class ConfirmOrReviseOutlineResponse(BaseModel):

    project_id:str 
    revision_task_id: Optional[str]
    status:ResearchProjectStatusType=Field(description="项目的状态")


class GenerateReportRequest(BaseModel):

    user_instruction: Optional[str] = Field(description="用户对生成报告的一些额外要求")

class GenerateReportResponse(BaseModel):

    task_id:str
    project_id:str
    task_type:TaskType
    status:ResearchProjectStatusType = Field(description="项目的状态")

class GetTaskStatusResponse(BaseModel):

    task_id:str
    project_id:str 
    task_type:TaskType
    status:TaskStatus = Field(description="当前异步任务的状态，")

    message :str = Field(description="可以在前端显示，当前任务进行到哪一步的消息")

    created_at:datetime
    updated_at: datetime


class Source(BaseModel):

    source_id:str
    title:str
    url : str
    published_at :str 

    source_type:str


class GetLatestReportResponse(BaseModel):

    project_id:str

    report_id:str

    version:int 

    title:str

    html:str 

    sources : list[Source]

    created_at:datetime