"""列出当前 key 可用的模型里，与 qwen2.5 / qwen3 / qwen-max 相关的条目。"""

import json
import sys
import urllib.request

sys.path.insert(0, "D:/EAG-GUARD/src")
from eag_guard.llm import client_from_env

client = client_from_env("D:/EAG-GUARD/.env")
req = urllib.request.Request(
    "https://dashscope.aliyuncs.com/compatible-mode/v1/models",
    headers={"Authorization": f"Bearer {client.api_key}"},
)
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode("utf-8"))

ids = sorted(m.get("id", "") for m in data.get("data", []))
print(f"共 {len(ids)} 个模型\n")

for keyword in ("qwen2.5", "qwen3", "qwen-max", "qwen-plus", "qwen-turbo", "qwen-long"):
    hits = [i for i in ids if keyword in i.lower()]
    print(f"--- {keyword}: {len(hits)}")
    for name in hits[:14]:
        print("   ", name)
