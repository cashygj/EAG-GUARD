"""统计 travel 的"部分命中"里，期望值中哪些片段没出现。"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.task_suite.load_suites import get_suite


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


run = Path(sys.argv[1])
domain = sys.argv[2]
suite = get_suite("v1", domain)

missing_kinds: Counter[str] = Counter()
samples: list[tuple[str, list[str]]] = []


def kind_of(part: str) -> str:
    low = part.lower()
    if re.fullmatch(r"[\d.]+", part):
        return "数字（评分/价格）"
    if re.search(r"rue|avenue|street|road|paris|london|\d{5}", low):
        return "地址"
    if re.search(r"\d{1,2}:\d{2}|am|pm|open", low):
        return "营业时间"
    if "@" in part:
        return "邮箱"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}|\d{4}-\d{2}-\d{2} \d{2}:\d{2}", part):
        return "日期"
    return "名称/其它"


for path in sorted(run.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error") or data["utility"]:
        continue
    task = suite.get_user_task_by_id(data["user_task"])
    truth = str(getattr(task, "GROUND_TRUTH_OUTPUT", "") or "")
    if not truth:
        continue
    answer = norm(data.get("final_answer") or "")
    parts = [p.strip() for p in re.split(r",(?![^(]*\))", truth) if p.strip()]
    missing = [p for p in parts if norm(p) and norm(p) not in answer]
    if not missing:
        continue
    for part in missing:
        missing_kinds[kind_of(part)] += 1
    if len(samples) < 3:
        samples.append((path.name.replace(".json", ""), missing))

print(f"{domain} 缺字段统计（按片段计）：")
for key, value in missing_kinds.most_common():
    print(f"  {key}: {value}")
print()
for name, missing in samples:
    print(f"  例 {name} 缺：{[m[:40] for m in missing][:5]}")
