# 1、调用ChatDeepSeek
import json
from openai import OpenAI
import os
from pydantic import BaseModel
client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key= os.environ["DEEPSEEK_API_KEY"]
)

# response = client.chat.completions.create(
#     model="deepseek-v4-flash",
#     messages=[{"role":"user","content":"帮我从这段话当中，提取出事件和时间: 小明下周一需要去公司开会, 以json格式输出"}],
#     response_format={'type': 'json_object'}
# )

# print(json.loads(response.choices[0].message.content))

class Event(BaseModel):
    event_name:str
    event_time:str

# 2、调用OpenAI
client = OpenAI(
    base_url="https://api.openai-proxy.org/v1",
    api_key= "sk-Zryi784ESlgEzfP37KzzHKD1vZb1FR9c6d3IijSGJsoRAfMu"
)



result = client.chat.completions.parse(
    model="gpt-5-mini",
    messages=[{"role":"user","content":"帮我从这段话当中，提取出事件和时间: 小明下周一需要去公司开会, 以json格式输出"}],
    response_format=Event
)

print(result.choices[0].message.parsed.model_dump(mode="json"))