from app.repository import research_project_repo

async def save_research_section(section: dict,project_id:str) -> dict:
    """
    供主智能体调用的工具，用以逐章节保存section，入参就是单章节的section，出参的dict，是返给主智能体 保存成功/失败信息（如果失败，需要告诉主智能体，因为什么原因失败）

    调用 research_project_repo把section保存到数据库当中去
    """

    
    try:
        # 1、校验 section，是否符合我们期望schema结构，以及从业务逻辑上，是否有问题；如果有问题，就将所有的问题，返回，让Agent修改，重新调用
        error_list = []
        section_id = section.get("section_id",None)
        # 1.1 是否有section_id
        if not section_id:
            error_list.append("当前传入的section，没有section id")

        project = await research_project_repo.get_project(project_id)

        outline = project["outline"]

        all_node_ids = research_project_repo.get_all_section_or_outline_ids(outline,type="outline")

        # 1.2 校验section_id，是否在大纲的叶子节点id当中
        if section_id not in all_node_ids:
            error_list.append(f"当前生成的section_id:{section_id}，不在大纲列表里面，重新生成")

        # 1.3 校验 模型是否生成了 title、summary、body、key_findings
        title = section.get("title")
        if not title:
            error_list.append("当前传入的section，没有title")

        summary = section.get("summary")
        if not summary:
            error_list.append("当前传入的section，没有摘要summary")

        key_findings = section.get("key_findings")

        all_sources = section.get("sources",[])

        all_source_ids = [source.get("source_id") for source in all_sources]
        
        if not type(key_findings) == list or not  key_findings :
            error_list.append("生成的section，关键发现（key_findings）必须要要是列表，且其中至少需要一条关键发现")
        else:
            all_key_findings_source = []

            for key_finding in key_findings:
                all_key_findings_source.extend(key_finding.get("source_ids"))


            if not set(all_key_findings_source).issubset(set(all_source_ids)):
                missing_set = set(all_key_findings_source) - set(all_source_ids)
                error_list.append(f"关键发现中，存在来源：{missing_set}, 在sources里面，不存在！请重新构造关键发现")


        if not type(section.get("risks")) == list :
            error_list.append("生成的section，风险点（risks）必须要要是列表，当没有风险时，输出空列表")
        else:
            risks = section.get("risks",[])
            all_risk_source = []
            for risk in risks:
                all_risk_source.extend(risk.get("source_ids"))

            if not set(all_risk_source).issubset(set(all_source_ids)):
                    missing_set = set(all_risk_source) - set(all_source_ids)
                    error_list.append(f"风险risks中，存在来源：{missing_set}, 在sources里面，不存在！请重新构造risks")


        if error_list:
            return {
                "status":False,
                "error_list":error_list
            }

        
        await research_project_repo.insert_section(section,project_id)

        return {
            "status":"ok"
        }
        
    except Exception as e:
        return {
            "status":False,
            "error_msg":str(e)
        }






    



        


        

    # 1.4 校验，模型输出的key_findings，以及risks里面的来源列表，是否存在模型幻觉

    


    


    

    # 1.2 当前的section_id，是否在outline大纲当中存在。


    

    



    # 2、如果没有任何问题，调用research_projects_repo.insert_section保存


