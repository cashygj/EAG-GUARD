"""结构性诊断：无防御下失败的对，到底卡在哪一步。

    python tools/undef_structure.py results/runs/banking_full_undefended
"""

import json
import sys
from collections import Counter
from pathlib import Path

run_dir = Path(sys.argv[1])
MAX_ITERS = 15

stats = Counter()
by_task: Counter[str] = Counter()
total = 0
for path in sorted(run_dir.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error"):
        continue
    total += 1
    if data["utility"]:
        stats["成功"] += 1
        continue
    calls = data.get("executed") or []
    task = path.name.split("_injection_")[0]
    by_task[task] += 1
    if not calls:
        stats["失败：一次工具都没调"] += 1
    elif len(calls) >= MAX_ITERS:
        stats["失败：撞轮次上限"] += 1
    elif len(calls) <= 2:
        stats["失败：只调了 1-2 次就收尾"] += 1
    else:
        stats["失败：调了多次但结果不对"] += 1

print(f"总数 {total}")
for key, value in stats.most_common():
    print(f"  {key:26s} {value:4d}  ({value / total:.0%})")
print("\n失败最多的任务：")
for task, count in by_task.most_common(8):
    print(f"  {task}: {count}")
