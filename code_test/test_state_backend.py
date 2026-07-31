from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from deepagents.backends.utils import create_file_data
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver
agent:CompiledStateGraph = create_deep_agent(
    model="deepseek:deepseek-v4-flash",
    tools=[],
    checkpointer=MemorySaver()
    # 默认使用的是state Back end 
    # backend=StateBackend()
)

test_txt_content = """
这是/test/test.txt 文件内部的内容
"""

# 第一次调用
result = agent.invoke(
    {
        "messages": [
            {"role": "user", "content": "帮我读取/test/test.txt文件当中的内容"}
        ],
        "files": {
            "/test/test.txt": create_file_data(test_txt_content),
        },
    },
    config={
        "configurable": {
            "thread_id": "demo-statebackend-skills"
        }
    },
)

second_result = agent.invoke(
    {
        "messages": [
            {"role": "user", "content": "再次帮我读取/test/test.txt文件当中的内容"}
        ],
    },
    config={
        "configurable": {
            "thread_id": "demo-statebackend-skills2"
        }
    },
)


print(second_result["messages"][-1])