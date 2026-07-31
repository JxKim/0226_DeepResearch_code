import os
from typing import Literal

from deepagents import create_deep_agent



# 声明式创建子智能体
research_subagent = {
    "name": "research-agent",
    "description": "Used to research more in depth questions",
    "system_prompt": "You are a great researcher",
    "model": "deepseek:deepseek-v4-flash",  # Optional override, defaults to main agent model
}
subagents = [research_subagent]

agent = create_deep_agent(
    model="deepseek:deepseek-v4-pro",
    subagents=subagents,
)

result  = agent.invoke(
    {"messages":[{"role":"user","content":"你有哪些子智能体，可以给你调用？"}]}
)

print(result["messages"][-1])