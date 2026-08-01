"""
所有agent相关的操作，都在该模块当中去定义，该模块，被backgroud所依赖
"""
from importlib.resources import read_text
from json import JSONDecodeError
from tkinter import EXCEPTION

from langchain.messages import AIMessage

from app.schemas.router_schema import ResearchBriefAndOutline, ResearchReport, ResearchResult,ResearchSection
from deepagents import SubAgent, create_deep_agent
from pathlib import Path
from app.config.config import Setting, get_setting
from app.tools.research_agent_tool import save_research_section
from app.tools.search_agent_tool import external_search, internal_knowledge_database_search, read_web_page
from app.repository import research_project_repo

from langgraph.checkpoint.memory import MemorySaver # 生产环境下，不可以使用MemorySaver，需要使用可持久化存储的checkpointer，例如Redis，Postgres
from deepagents.backends.utils import create_file_data
root_dir = get_setting().root_dir
class ResearchAgent:

    def __init__(self) -> None:
        main_agent_system_prompt_path = root_dir/ "agents" / "prompts" / "research_manager.md"
        search_agent_system_prompt_path = root_dir / "agents" / "prompts" / "search_agent.md"

        search_sub_agent = {
            "name":"information-search-agent", # 子智能体的名称,
            "description":"专门用于检索信息的子智能体，可以对单个原子问题，搜索互联网公开信息和内部知识库信息，检索结果", # 子智能的作用描述，会作为提示词，给到主智能体
            "system_prompt":search_agent_system_prompt_path.read_text(encoding="UTF-8"), # 子智能体的system prompt
            "tools":[external_search, internal_knowledge_database_search, read_web_page], # 子智能体所能够调用的工具
            "model":"deepseek:deepseek-v4-flash"  # 子智能体所使用的模型，子智能体可以使用一个稍小的模型
        }
        subagent  = [search_sub_agent,]
        self.manager_agent = create_deep_agent(
            model="deepseek:deepseek-v4-pro", # 主智能体所使用的model，通过这种方式传入model_id，deepagents底层会创建ChatDeepSeek的实例，其内部已经有了DEEPSEEK_BASE_URL, 需要额外维护的环境变量：DEEPSEEK_API_KEY
            system_prompt=main_agent_system_prompt_path.read_text(encoding="UTF-8"), # 主智能体的system prompt
            tools=[save_research_section], # 主智能体，所使用的工具
            subagents=subagent,
            # middleware=[] # deepagents，内部自带了多个关键的中间件，例如 TODOLIST, FILESYSTEM, SUBAGENT, SUMMARIZATION等
            checkpointer=MemorySaver()
        )

    async def generate_brief_and_outline(self,project_id:str) -> ResearchBriefAndOutline:
        """
        基于project_id，读到当前研究项目，基于研究项目中的设定，生成任务书和大纲
        """
        # 1、基于project_id，通过repo读到用户的request（主题，目标，地域范围，时间范围等信息）
        project = await research_project_repo.get_project(project_id)
        user_request = project["request"]
        task_dict = {
            "task_type":"generate_brief_and_outline",
            "user_request":user_request,
            "project_id":project_id,
        }
        try:
            # 2、调用manager_agent，让agent,以json形式，输出大纲和任务书
            result:dict = await self.manager_agent.ainvoke(
                {
                    "messages":[
                        {"role":"user","content":"查看下/research/task_payload.json 任务，并完成"}
                    ],
                    "files":{
                        "/research/task_payload.json": create_file_data(task_dict)
                    }
                },
                config={
                    "configurable":{
                        "thread_id":f"{project_id}:generate_brief_and_outline"
                    }
                }
            )

            all_message_list:list = result["messages"]

            ai_message:AIMessage = all_message_list[-1]

            ai_message_content:str=ai_message.content

            import json
            # 如何让大模型稳定输出JSON
            # 1.在prompt当中，约束模型必须输出JSON，给模型一个json 示例

            # 2.利用厂商的模型输出JSON的能力，在调用厂商接口的时候，指定，必须输出JSON ,(部分厂商还能够直接指定输出的JSON的schema)

            # 3. 对于像DeepSeek这种厂商，不允许指定，输出的JSON的结构，可以使用tools来让模型巧妙输出特定结构JSON
            dict_result = json.load(ai_message_content)

            research_brief_and_outline:ResearchBriefAndOutline =  ResearchBriefAndOutline.model_validate(dict_result)

            await research_project_repo.insert_brief_and_outline(project_id,research_brief_and_outline )
        except JSONDecodeError as e:
            # 当大模型输出的不是一个合法的JSON的时候，处理方式：
                # 1、重试
                # 2、配置一个默认值
                research_brief_and_outline = ResearchBriefAndOutline()


        return research_brief_and_outline



        # 3、再次调用repo，将大纲和任务书保存到数据库当中
        

    async def revise_outline(self, project_id:str, revision_instruction:str) -> ResearchBriefAndOutline:
        """
        基于project_id，读到当前研究项目，基于研究项目中的设定、原大纲和任务书，和用户传入的修改意见，修改任务书和大纲，并且返回新的任务书和大纲 实例（ResearchBriefAndOutline）
        """

        # 1、基于project_id，通过repo读到用户的request（主题，目标，地域范围，时间范围等信息）
                project = await research_project_repo.get_project(project_id)
                user_request = project["request"]
                current_outline = project["outline"]
                current_brief = project["research_brief"]
                task_dict = {
                    "task_type":"generate_brief_and_outline",
                    "user_request":user_request,
                    "current_outline":current_outline,
                    "current_brief":current_brief,
                    "revision_instruction":revision_instruction
                }
                try:
                    # 2、调用manager_agent，让agent,以json形式，输出大纲和任务书
                    result:dict = await self.manager_agent.ainvoke(
                        {
                            "messages":[
                                {"role":"user","content":"查看下/research/task_payload.json 任务，并完成"}
                            ],
                            "files":{
                                "/research/task_payload.json": create_file_data(task_dict)
                            }
                        },
                        config={
                            "configurable":{
                                "thread_id":f"{project_id}:revise_outline"
                            }
                        }
                    )
        
                    all_message_list:list = result["messages"]
        
                    ai_message:AIMessage = all_message_list[-1]
        
                    ai_message_content:str=ai_message.content
        
                    import json
                    # 如何让大模型稳定输出JSON
                    # 1.在prompt当中，约束模型必须输出JSON，给模型一个json 示例
        
                    # 2.利用厂商的模型输出JSON的能力，在调用厂商接口的时候，指定，必须输出JSON ,(部分厂商还能够直接指定输出的JSON的schema)
        
                    # 3. 对于像DeepSeek这种厂商，不允许指定，输出的JSON的结构，可以使用tools来让模型巧妙输出特定结构JSON
                    dict_result = json.load(ai_message_content)
        
                    research_brief_and_outline:ResearchBriefAndOutline =  ResearchBriefAndOutline.model_validate(dict_result)


                    await research_project_repo.insert_brief_and_outline(project_id,research_brief_and_outline )


                except JSONDecodeError as e:
                    # 当大模型输出的不是一个合法的JSON的时候，处理方式：
                        # 1、重试
                        # 2、配置一个默认值
                        research_brief_and_outline = ResearchBriefAndOutline()
        
        
                return research_brief_and_outline



    async def generate_sections(self, project_id:str,user_instruction:str) -> list[ResearchSection]:
        """
        基于project_id，读到当前研究项目，基于已经确认的大纲和任务书，让agent逐章节生成 章节的具体内容，将所有章节的内容，返回
        """
        # 1.基于project_id,读到项目,读到其中的任务书research_brief,和outline
        project:dict = await research_project_repo.get_project(project_id)
        research_brief:dict = project["research_brief"]
        outline:list[dict] = project["outline"]
        user_request = project["request"]
        missing_sections_ids :list[str] = research_project_repo.get_all_section_or_outline_ids(outline,type="outline")
        task_dict = {
             "task_name":"generate_sections",
             "research_brief":research_brief,
             "outline":outline,
             "project_id":project_id,
             "user_request":user_request,
             # 为了避免,agent,没有写完所有的章节,就提前结束了,我们给模型N次机会,每次模型调用完成,我们去基于outline大纲,和该project已生成的sections,来得到缺失的sections
             # 在下一次调用agent时,让模型完成缺失的sections的编写; missing_sections,传的是一个列表,表示模型没有完成的叶子节点章节的章节ID,例如[1.1, 1.3, 1.5, 2.1]
             "missing_sections":missing_sections_ids
        }
        # 2.调用模型,让模型在调用过程当中,逐章保存section

        # 大模型的问题:提前说完成了
        for i in range(Setting.agent_retry_times):
            # 1. 让模型生成missing_sections当中的章节
            task_dict = {
                         "task_name":"generate_sections",
                         "research_brief":research_brief,
                         "project_id":project_id,
                         "outline":outline,
                         "user_request":user_request,
                         # 为了避免,agent,没有写完所有的章节,就提前结束了,我们给模型N次机会,每次模型调用完成,我们去基于outline大纲,和该project已生成的sections,来得到缺失的sections
                         # 在下一次调用agent时,让模型完成缺失的sections的编写; missing_sections,传的是一个列表,表示模型没有完成的叶子节点章节的章节ID,例如[1.1, 1.3, 1.5, 2.1]
                         "missing_sections":missing_sections_ids
            }
            await self.manager_agent.ainvoke(
                {
                    "messages":[{"role":"user","content":"查看下/research/task_payload.json 任务，并完成"}],
                    "files":{
                                                    "/research/task_payload.json": create_file_data(task_dict)
                                                }
                },
                config={
                    "configurable":{
                        "thread_id":f"{project_id}:generate_sections"
                    }
                }
            )

            # 2.校验,该project下面的所有章节是否生成完成
            project :dict = await research_project_repo.get_project(project_id)

            current_sections:list[dict]  = project["sections"]

            current_sections_ids:list[str] = research_project_repo.get_all_section_or_outline_ids(current_sections,type="sections")

            # outline_node_ids是大纲当中的所有叶子节点的ids

            missing_sections_ids  = list(set(missing_sections_ids) - set(current_sections_ids))

            if not missing_sections_ids:
                 break

    @staticmethod
    def _section_finding_claims(section: ResearchSection) -> list[str]:
        return [finding.claim for finding in section.key_findings if finding.claim.strip()]

    @staticmethod
    def _section_risk_descriptions(section: ResearchSection) -> list[str]:
        return [risk.description for risk in section.risks if risk.description.strip()]

    def _dedupe_texts(self, values: list[str]) -> list[str]:
        """按原顺序去重文本列表。"""

        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            text = str(value or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            deduped.append(text)
        return deduped
    
    def _build_executive_summary(self, sections: list[ResearchSection]) -> ResearchSynthesis:
        """从已完成章节确定性生成全局研究综合。"""

        core_conclusions: list[str] = []
        cross_section_insights: list[str] = []
        strategic_recommendations: list[str] = []
        global_risks: list[str] = []
        for section in sections:
            finding_claims = self._section_finding_claims(section)
            risk_descriptions = self._section_risk_descriptions(section)
            if section.summary:
                core_conclusions.append(section.summary)
            core_conclusions.extend(finding_claims[:2])
            if section.summary or finding_claims:
                cross_section_insights.append(
                    f"{section.title}: {section.summary or finding_claims[0]}"
                )
            global_risks.extend(risk_descriptions[:2])

        unique_conclusions = self._dedupe_texts(core_conclusions)[:8]
        unique_insights = self._dedupe_texts(cross_section_insights)[:8]
        unique_risks = self._dedupe_texts(global_risks)[:8]
        if unique_conclusions:
            executive_summary = "；".join(unique_conclusions[:6])
        else:
            executive_summary = "本报告基于已确认大纲逐章节完成研究。"
        return executive_summary
    
    async def generate_report(self, sections: list[ResearchSection],topic:str) -> ResearchReport:
        """
        基于各个章节的内容，进行渲染，得到最终的报告
        """

        # 1、基于数据库当中sections，合并所有的sections的source，构建全局的sources 来源列表
        all_source_dict= {} # key是每个source所对应的url地址,value是source全局的编号
        all_source_list = []
        source_num = 0

        for section in sections:
             source_list = section.sources

             for source in source_list:
                  if source.url in all_source_dict.keys():
                       source.source_id = all_source_dict[source.url]
                  else:
                       source.source_id = str(source_num)
                       all_source_dict[source.url] = str(source_num)
                       source_num +=1
                       all_source_list.append(source)

        # 2、把来源列表，sections等内容，构建成一个用于渲染的ResearchResult对象
        executive_summary = self._build_executive_summary(sections)
        research_result = ResearchResult(
             title=f"{topic}研究报告",
             executive_summary= executive_summary,
             sections=sections,
             sources=all_source_list
        )

        # 3、基于ResearchResult渲染一个html文件
        # 参考完整项目代码当中的渲染逻辑，涉及到较多HTML的渲染


research_agent = None


def get_agent():

    global research_agent
    if research_agent is None:

        research_agent = ResearchAgent()

    return research_agent

    
