from fastapi import FastAPI
import requests
ragflow_url = "http://localhost:80/api/v1/retrieval"

payload: dict = {
        "question": "晶圆制造",
        "page": max(1, 1),
        "page_size": max(1, min(10, 30)),
        "similarity_threshold": max(0.0, min(0.7, 1.0)),
        "vector_similarity_weight": max(0.0, min(0.5, 1.0)),
        "top_k": max(1, 1),
        "dataset_ids":["60be664867a011f1af5d8b7d6367b4b2"]
    }

headers = {
    "Authorization":"Bearer codex-local-ragflow-token"
}
result = requests.post(ragflow_url,json=payload,headers=headers)
import json
print(json.dumps(result.json(),ensure_ascii=False))
