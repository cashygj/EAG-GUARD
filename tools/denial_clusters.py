"""把回归集里的失败按"拦截原因"聚类，找系统性成因。"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

RUNS = Path(r"D:\EAG-GUARD\results\runs")
MANIFEST = json.loads(Path(r"D:\EAG-GUARD\results\regression_set.json").read_text(encoding="utf-8"))

RULES = [
    ("工具不在 T", r"不在授权范围 T"),
    ("对象不在 O", r"不在授权范围 O"),
    ("参数只可溯源到不可信", r"只可溯源到不可信"),
    ("URL 未委托", r"未被委托|不在用户请求"),
    ("跨切片不一致", r"不同的记录"),
    ("其它", r"."),
]


def classify(reason: str) -> str:
    for name, pattern in RULES:
        if re.search(pattern, reason):
            return name
    return "其它"


buckets = Counter()
detail: dict[str, list[str]] = {}
no_denial = Counter()

for domain, pairs in MANIFEST.items():
    run = RUNS / f"reg_{domain}"
    if not run.exists():
        continue
    for pair in pairs:
        path = run / f"{domain}_{pair['user_task']}_{pair['injection_task']}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["utility"]:
            continue
        steps = (data.get("guard") or {}).get("steps") or []
        denials = [s for s in steps if not s["allowed"]]
        if not denials:
            no_denial[domain] += 1
            continue
        for step in denials:
            for reason in step["reasons"] or ["（无理由）"]:
                kind = classify(reason)
                buckets[kind] += 1
                detail.setdefault(kind, []).append(
                    f"{domain} {pair['user_task']}×{pair['injection_task']}: {reason[:80]}")

print("拦截原因分布：")
for kind, count in buckets.most_common():
    print(f"  {kind}: {count}")
print()
print("没有拦截却失败的：", dict(no_denial))
print()
for kind, _ in buckets.most_common(3):
    print(f"--- {kind} 样例")
    for line in detail[kind][:4]:
        print("   ", line)
