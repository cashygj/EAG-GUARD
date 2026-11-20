"""slack 失败画像：拦截 vs 模型侧，以及被拦的具体动作。"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.task_suite.load_suites import get_suite

run = Path(sys.argv[1])
suite = get_suite("v1", "slack")

touched = Counter()
denial_tools = Counter()
denial_reasons = Counter()
samples = {}

for path in sorted(run.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error") or data["utility"]:
        continue
    steps = (data.get("guard") or {}).get("steps") or []
    denials = [s for s in steps if not s["allowed"]]
    if not denials:
        touched["失败但无拦截（模型侧）"] += 1
        continue
    touched["失败且有拦截"] += 1
    names = set()
    for step in denials:
        tool = step["action"].split("(")[0]
        names.add(tool)
        denial_tools[tool] += 1
        reason = (step["reasons"][0] if step["reasons"] else "无理由")
        kind = ("裁判判定扩权/链路不符" if "用户请求" in reason or "授权说明" in reason
                else "参数无法归因" if "无法归因" in reason or "只可溯源" in reason
                else "工具不在 T" if "不在授权范围 T" in reason
                else "对象不在 O" if "不在授权范围 O" in reason
                else "其它")
        denial_reasons[kind] += 1
        samples.setdefault(kind, f"{path.stem}: {reason[:90]}")

total = sum(touched.values())
print(f"{run.name}: 失败 {total} 对")
for key, value in touched.most_common():
    print(f"  {key}: {value} ({value/total:.0%})")
print()
print("被拦工具 top：")
for tool, count in denial_tools.most_common(6):
    print(f"  {tool}: {count}")
print()
print("拦截理由分布：")
for kind, count in denial_reasons.most_common():
    print(f"  {kind}: {count}")
    if kind in samples:
        print(f"      例：{samples[kind]}")
