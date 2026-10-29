import json
from collections import Counter
from pathlib import Path

run = Path(r"D:\EAG-GUARD\results\runs\travel_v2_eag")
tasks = Counter()
samples = []
for path in sorted(run.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    for step in (data.get("guard") or {}).get("steps") or []:
        if step["allowed"]:
            continue
        reason = step["reasons"][0] if step["reasons"] else ""
        if "不在授权范围 T" in reason and "reserve_" in reason:
            tasks[path.name.split("_injection_")[0]] += 1
            if len(samples) < 5:
                samples.append((path.name, step["action"][:80], reason[:80]))

for task, count in tasks.most_common():
    print(f"{task}: {count}")
print()
for name, action, reason in samples:
    print(name, "|", action)
