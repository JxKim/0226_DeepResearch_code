"""
所有agent相关的操作，都在该模块当中去定义，该模块，被backgroud所依赖
"""
from app.schemas.router_schema import ResearchBriefAndOutline, ResearchReport,ResearchSection



class ResearchAgent:

    async def generate_brief_and_outline(self,project_id:str) -> ResearchBriefAndOutline:
        """
        基于project_id，读到当前研究项目，基于研究项目中的设定，生成任务书和大纲
        """

        pass

    async def revise_outline(self, project_id:str, revision_instruction:str) -> ResearchBriefAndOutline:
        """
        基于project_id，读到当前研究项目，基于研究项目中的设定、原大纲和任务书，和用户传入的修改意见，修改任务书和大纲，并且返回新的任务书和大纲 实例（ResearchBriefAndOutline）
        """

    async def generate_sections(self, project_id:str,user_instruction:str) -> list[ResearchSection]:
        """
        基于project_id，读到当前研究项目，基于已经确认的大纲和任务书，让agent逐章节生成 章节的具体内容，将所有章节的内容，返回

        """

    async def generate_report(self, sections: list[ResearchSection]) -> ResearchReport:
        """
        基于各个章节的内容，进行渲染，得到最终的报告
        """


research_agent = None


def get_agent():

    global research_agent
    if research_agent is None:

        research_agent = ResearchAgent()

    return research_agent

    
