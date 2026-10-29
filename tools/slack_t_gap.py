"""统计 slack 全域里被拦的 send_direct_message 出现在哪些任务、原因是什么。"""

import json
from collections import Counter
from pathlib import Path

run = Path(r"D:\EAG-GUARD\results\runs\slack_full_eag")
by_task: Counter[str] = Counter()
samples = []
for path in sorted(run.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    user_task = path.name.split("_injection_")[0]
    for step in (data.get("guard") or {}).get("steps") or []:
        if step["allowed"]:
            continue
        reason = step["reasons"][0] if step["reasons"] else ""
        if "不在授权范围 T" in reason and "send_direct_message" in reason:
            by_task[user_task] += 1
            if len(samples) < 6:
                samples.append((path.name, step["action"][:90], reason[:90]))

print("按任务统计 send_direct_message 被拦次数：")
for task, count in by_task.most_common():
    print(f"  {task}: {count}")
print("\n样例：")
for name, action, reason in samples:
    print(f"  {name}: {action}")
    print(f"     {reason}")
