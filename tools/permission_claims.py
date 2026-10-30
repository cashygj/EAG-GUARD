"""统计"模型自称没权限/无法访问"的失败对——这是工具输出没被读懂时的典型表现。"""

import json
import re
import sys
from pathlib import Path

PATTERNS = re.compile(
    r"don'?t have (?:permission|access)|cannot access|can'?t access|no permission|"
    r"无法(?:直接)?(?:查看|访问|读取)|没有权限|系统限制|not able to (?:view|access)",
    re.I,
)

for name in sys.argv[1:]:
    run = Path(name)
    if not run.exists():
        continue
    total = hit = 0
    samples = []
    for path in run.glob("*.json"):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("error") or data["utility"]:
            continue
        total += 1
        answer = data.get("final_answer") or ""
        if PATTERNS.search(answer):
            hit += 1
            if len(samples) < 3:
                samples.append(path.name.replace(".json", ""))
    print(f"{run.name:18s} 失败 {total:3d} 对，其中自称无权限 {hit:2d}")
    for sample in samples:
        print("      ", sample)
