"""
子智能体的工具定义
"""

from ast import parse
from urllib.request import urlopen
import httpx
from app.config.config import get_setting

setting = get_setting()

class _ReadableHtmlParser(HTMLParser):
    """轻量 HTML 正文提取器，跳过脚本、样式和导航噪音标签。"""

    def __init__(self) -> None:
        super().__init__()
        self.text_parts: list[str] = []
        self.title: str | None = None
        self.published_at: str | None = None
        self._ignored_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg", "nav", "footer"}:
            self._ignored_depth += 1
            return
        if tag == "title":
            self._in_title = True
            return
        if tag == "meta":
            self._handle_meta(attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg", "nav", "footer"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)
            return
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        normalized = _normalize_space(data)
        if not normalized:
            return
        if self._in_title:
            self.title = normalized
            return
        if self._ignored_depth == 0:
            self.text_parts.append(normalized)

    def _handle_meta(self, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key.lower(): value for key, value in attrs if value is not None}
        meta_key = (attr_map.get("property") or attr_map.get("name") or "").lower()
        content = attr_map.get("content")
        if meta_key in {"article:published_time", "datepublished", "pubdate", "date"} and content:
            self.published_at = content


async def external_search(query:str, start_date:str, end_date:str,include_domains:list,exclude_domains:list ) -> dict:
    """
    外部搜索的工具，搜索互联网的公开信息
    """
    payload = {
        "query":query,
        "max_results":5,
        "start_date":start_date,
        "end_date":end_date,
        "include_domains":include_domains if include_domains else [],
        "include_raw_content":False,
        "exclude_domains": exclude_domains if exclude_domains else []

    }

    try:

        async with httpx.AsyncClient(timeout=setting.http_time_out) as client:

            response = await client.post(
                url="https://api.tavily.com/search",
                headers={
                    "Authorization":f"Bearer {setting.tavily_token}",
                    "Content-Type":"applcation/json"
                },
                json= payload

            )

    # json_data的结构,如下:
    #         {
    #   "query": "Who is Leo Messi?",
    #   "answer": "Lionel Messi, born in 1987, is an Argentine footballer widely regarded as one of the greatest players of his generation. He spent the majority of his career playing for FC Barcelona, where he won numerous domestic league titles and UEFA Champions League titles. Messi is known for his exceptional dribbling skills, vision, and goal-scoring ability. He has won multiple FIFA Ballon d'Or awards, numerous La Liga titles with Barcelona, and holds the record for most goals scored in a calendar year. In 2014, he led Argentina to the World Cup final, and in 2015, he helped Barcelona capture another treble. Despite turning 36 in June, Messi remains highly influential in the sport.",
    #   "images": [],
    #   "results": [
    #     {
    #       "title": "Lionel Messi Facts | Britannica",
    #       "url": "https://www.britannica.com/facts/Lionel-Messi",
    #       "content": "Lionel Messi, an Argentine footballer, is widely regarded as one of the greatest football players of his generation. Born in 1987, Messi spent the majority of his career playing for Barcelona, where he won numerous domestic league titles and UEFA Champions League titles. Messi is known for his exceptional dribbling skills, vision, and goal",
    #       "score": 0.81025416,
    #       "raw_content": null,
    #       "favicon": "https://britannica.com/favicon.png",
    #       "images": [
    #         {
    #           "url": "<string>",
    #           "description": "<string>"
    #         }
    #       ]
    #     }
    #   ],
    #   "response_time": "1.67",
    #   "auto_parameters": {
    #     "topic": "general",
    #     "search_depth": "basic"
    #   },
    #   "usage": {
    #     "credits": 1
    #   },
    #   "request_id": "123e4567-e89b-12d3-a456-426614174111"
    # }
            response.raise_for_status()
            json_data = response.json()

            results_list:list[dict] = json_data["results"]

            # 对数据做清洗
            output_results= [{"title":result["title"],"content":result["content"],"url":result["url"]} for result in results_list]

    except Exception as e:
        error_msg  = str(e)
        # 当工具调用抛出异常，需要将异常信息给模型，让模型判断，是 调用工具入参问题 / 工具本身问题，从而让模型决定，是否需要调用重试
        return {
            "status":False,
            "error_msg":error_msg
        }
    else:

        return {
            "status":"ok",
            "search_result":output_results
        }


async def read_web_page(url:str,max_chars:int) -> dict:
    """
    可以让模型自行去决定 读取某个url所对应的网页当中 特定字符数量的 详细的网页内容
    """
    try:

        with urlopen(url=url, timeout=setting.http_time_out) as response:
            html = response.read().decode(encoding = "UTF-8")
        parser = _ReadableHtmlParser()

        parser.feed(html)

        limited_content = "".join(parser.text_parts)[:max_chars]

        return {
            "status":"ok",
            "limited_content":limited_content,
            "published_at":parser.published_at,
            "title":parser.title,
            "source_type":"public_web"
        }
    except Exception as e:
        return {
            "status":False,
            "error_msg":str(e),
            
        }



        
# 
async def internal_knowledge_database_search(query:str,page:int, page_size,similarity_threshold:float,vector_similarity_weight:float,top_k:int):
    """
    内部知识库搜索工具
    """
    ragflow_base_url:str = setting.ragflow_base_url
    rag_flow_url = ragflow_base_url + "/api/v1/retrieval"

    payload: dict = {
        "question": query,
        "page": max(1, page),
        "page_size": max(1, min(page_size, 30)),
        "similarity_threshold": max(0.0, min(similarity_threshold, 1.0)),
        "vector_similarity_weight": max(0.0, min(vector_similarity_weight, 1.0)),
        "top_k": max(1, top_k),
        "dataset_ids":setting.dataset_id
    }
    try:

        async with httpx.AsyncClient(timeout=setting.http_time_out) as client :

            result = await client.post(
                rag_flow_url,
                json=payload
            )

            result.raise_for_status()

            data = result.json()

            chunks_list = data["data"]["chunks"]

            chunk_result_list = [chunk["content"] for chunk in chunks_list]

            return {
                "status":"ok",
                "result_content":chunk_result_list, # 在chunk_result_list当中的每个chunk，添加一个"url": ，后面用于做全局的source去重，这个url，可以是chunk所对应的file_name/document_name ，这个名字，在RAGFLOW里面是维护了的
                "source_type":"internal_knowledge_base",
               
            }

    except Exception as e:
        err_msg = str(e)
        return {
            "status":False,
            "error_msg":err_msg
        }