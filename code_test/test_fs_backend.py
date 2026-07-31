from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
backend = FilesystemBackend(
    root_dir="/home/m1881/pycharm_projects/0226_DeepResearch"
)

agent = create_deep_agent(
    model="deepseek:deepseek-v4-flash",
    tools=[],
    backend=backend,
    checkpointer=MemorySaver()
)

result = agent.invoke(
    {
        "messages": [
            {"role": "user", "content": "帮我读取一下当前目录下面的README.md文件，看下里面的内容是什么"}
        ],
    },
    config={
        "configurable": {
            "thread_id": "demo-filesystembackend-skills"
        }
    },
)


result2 = agent.invoke(
    {
        "messages": [
            {"role": "user", "content": "帮我读取一下当前目录下面的README.md文件，看下里面的内容是什么"}
        ],
    },
    config={
        "configurable": {
            "thread_id": "demo-filesystembackend-skills2"
        }
    },
)

print(result2["messages"][-1])