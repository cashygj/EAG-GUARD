"""探测当前 key 上哪些模型可用（最小请求，几毛钱以内）。"""

import sys
from pathlib import Path

sys.path.insert(0, "D:/EAG-GUARD/src")
from eag_guard.llm import client_from_env

client = client_from_env("D:/EAG-GUARD/.env")

CANDIDATES = [
    "qwen2.5-27b-instruct",
    "qwen2.5-32b-instruct",
    "qwen2.5-14b-instruct",
    "qwen2.5-72b-instruct",
    "qwen2.5-7b-instruct",
    "qwen-plus-2025-04-28",
]

for name in CANDIDATES:
    try:
        reply = client.complete("只回复 OK", model=name, temperature=0.0)
        print(f"{name:28s} OK  -> {str(reply)[:20]!r}")
    except Exception as exc:                       # noqa: BLE001
        text = str(exc).replace("\n", " ")[:120]
        print(f"{name:28s} 失败 -> {text}")
