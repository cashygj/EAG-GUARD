"""把 slack 的拦截分成两类：

A. **误杀**：被拦的工具在无防御臂里被成功执行过（= 任务真的需要它）；
B. **正确拦截**：被拦的工具无防御臂也没用过（= 注入要求的动作），任务失败是"拦后没恢复"。
"""

import json
import sys
from pathlib import Path

guard_run = Path(sys.argv[1])
undef_run = Path(sys.argv[2])

undef_tools: dict[str, set[str]] = {}
for path in undef_run.glob("*.json"):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    undef_tools[path.name] = {c["function"] for c in (data.get("executed") or [])}

buckets = {"A 误杀（任务需要却被拦）": 0, "B 正确拦截（注入动作）": 0, "C 混合": 0}
detail = {"A": [], "B": [], "C": []}

for path in sorted(guard_run.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error") or data["utility"]:
        continue
    steps = (data.get("guard") or {}).get("steps") or []
    denials = [s["action"].split("(")[0] for s in steps if not s["allowed"]]
    if not denials:
        continue
    needed = undef_tools.get(path.name, set())
    false_denials = [tool for tool in denials if tool in needed]
    if false_denials and len(false_denials) == len(set(denials)):
        buckets["A 误杀（任务需要却被拦）"] += 1
        detail["A"].append(f"{path.stem}: {sorted(set(false_denials))}")
    elif false_denials:
        buckets["C 混合"] += 1
        detail["C"].append(f"{path.stem}: 误杀{ sorted(set(false_denials)) } / 正确{ sorted(set(denials) - set(false_denials)) }")
    else:
        buckets["B 正确拦截（注入动作）"] += 1
        detail["B"].append(f"{path.stem}: {sorted(set(denials))}")

print(f"{guard_run.name} 对照 {undef_run.name}")
for key, value in buckets.items():
    print(f"  {key}: {value}")
print()
for key in ("A", "C"):
    if detail[key]:
        print(f"--- {key} 类样例")
        for line in detail[key][:6]:
            print("   ", line)
