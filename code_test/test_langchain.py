from sre_parse import State
from typing import TypedDict

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware,TodoListMiddleware
from deepagents import FilesystemMiddleware, create_deep_agent

from langgraph.graph import StateGraph

FilesystemMiddleware
class MyState(TypedDict):

    messages:list[str]
    test_state:str


def node_a(state:MyState):


    return {
        "test_state": "变更后的test_State"
    }




graph = StateGraph(MyState)

graph.add_node("xxx",xxx)
graph.add_edge("xxx","xxx")

complied_graph  = graph.compile()

result = complied_graph.invoke()

# agent = create_agent()
agent = create_deep_agent()