from langchain.messages import AIMessage
from langchain_deepseek import ChatDeepSeek
from langchain.tools import tool

llm = ChatDeepSeek(
    model="deepseek-v4-flash"
)

@tool
def get_args(event_time:str, event_name:str):
    """
    调用该工具,输出event_time, event_name
    """
    print(f"模型调用的入参:{event_time}",f", event_time为:{event_time}")


llm_with_tools  = llm.bind_tools([get_args])


result:AIMessage = llm_with_tools.invoke(
    [
                {"role":"user","content":"帮我从这段话当中，提取出事件和时间: 小明下周一需要去公司开会, 调用get_args工具,输出"}
            ]
)

print(result.tool_calls[0]["args"])