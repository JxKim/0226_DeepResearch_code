from deepagents import create_deep_agent
from deepagents.backends import StoreBackend
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

skill_md = """---
name: web-research
description: 用于公开资料检索、来源整理和结论归纳
---

# Web Research

当用户要求调研某个主题时：
1. 明确问题范围
2. 收集来源
3. 整理关键事实
4. 输出带来源的总结
"""

namespace = ("user-123", "agent-files")

# 先把 skill 文件写入 LangGraph store
store.put(
    namespace,
    "/skills/project/web-research/SKILL.md",
    {
        "content": skill_md,
        "encoding": "utf-8",
    },
)

backend = StoreBackend(
    store=store,
    namespace=lambda rt: namespace,
)

agent = create_deep_agent(
    model="deepseek:deepseek-v4-flash",
    tools=[],
    backend=backend,
    store=store,
    skills=["/skills/project/"],
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "帮我读取一下，我的/skills/project/web-research/SKILL.md 内部的内容",
            }
        ],
    },
    config={
        "configurable": {
            "thread_id": "demo-storebackend-skills"
        }
    },
)

print(result["messages"][-1])