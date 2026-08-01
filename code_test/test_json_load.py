import json

json_str = """
{
"key1":"value1"

"""

res = json.loads(json_str)

print(res)