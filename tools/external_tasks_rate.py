"""看外部频道那 4 个任务在三个臂里的通过率。"""

import json
from collections import defaultdict
from pathlib import Path

RUNS = Path(r"D:\EAG-GUARD\results\runs")
TARGETS = ("user_task_7", "user_task_9", "user_task_10", "user_task_12")

for name in ("slack_full_undefended", "final_slack", "q35_slack_full"):
    run = RUNS / name
    if not run.exists():
        continue
    stat = defaultdict(lambda: [0, 0])
    for path in run.glob("*.json"):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        stat[data["user_task"]][0] += 1
        stat[data["user_task"]][1] += bool(data["utility"])
    parts = [
        f"{task.replace('user_task_', '')}:{stat[task][1]}/{stat[task][0]}"
        for task in TARGETS if stat[task][0]
    ]
    print(f"{name:24s} " + "  ".join(parts))
