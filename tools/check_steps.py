import json
from pathlib import Path

run = Path(r"D:\EAG-GUARD\results\runs\snap105v4_eag")
for task in (8, 9, 10, 13, 14):
    path = run / f"slack_user_task_{task}_injection_task_1.json"
    if not path.exists():
        print(f"task {task}: missing")
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    steps = data.get("guard", {}).get("steps", [])
    denied = [s for s in steps if not s["allowed"]]
    print(f"task {task}: util={data['utility']} steps={len(steps)} denied={len(denied)}")
    for step in denied[:2]:
        reason = step["reasons"][0] if step["reasons"] else ""
        print(f"    [{step['action'][:70]}] {reason[:110]}")
