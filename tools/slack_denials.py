"""看 slack 里"对象不在 O"和"其它"两类拦截的具体分布。"""

import json
from collections import Counter
from pathlib import Path

run = Path(r"D:\EAG-GUARD\results\runs\slack_full_eag")
obj_cases = Counter()
other_cases = Counter()
samples_obj = []
samples_other = []

for path in sorted(run.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    for step in (data.get("guard") or {}).get("steps") or []:
        if step["allowed"]:
            continue
        reason = step["reasons"][0] if step["reasons"] else ""
        if "不在授权范围 O" in reason:
            obj_cases[path.name.split("_injection_")[0]] += 1
            if len(samples_obj) < 4:
                samples_obj.append((path.name, step["action"][:80], reason[:110]))
        elif "执行链" in reason or "未被委托" in reason:
            other_cases[path.name.split("_injection_")[0]] += 1
            if len(samples_other) < 4:
                samples_other.append((path.name, step["action"][:80], reason[:110]))

print("=== 对象不在 O ===")
for task, count in obj_cases.most_common(6):
    print(f"  {task}: {count}")
for name, action, reason in samples_obj:
    print(f"  {name}\n    {action}\n    {reason}")

print("\n=== 链接/执行链 ===")
for task, count in other_cases.most_common(6):
    print(f"  {task}: {count}")
for name, action, reason in samples_other:
    print(f"  {name}\n    {action}\n    {reason}")
