#!/usr/bin/env python
"""按用户任务统计效用，看差距集中在哪些任务上。

    python tools/per_user_task.py results/runs/snap_slack105_eag
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


def main() -> int:
    run_dir = Path(sys.argv[1])
    per_task: dict[str, list[bool]] = defaultdict(list)
    for path in sorted(run_dir.glob("*.json")):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("error"):
            continue
        per_task[data["user_task"]].append(bool(data["utility"]))

    print(f"{'任务':14s} {'对数':>4s} {'完成':>4s} {'UA':>7s}")
    for task in sorted(per_task, key=lambda t: int(t.split("_")[-1])):
        results = per_task[task]
        done = sum(results)
        bar = "█" * done + "·" * (len(results) - done)
        print(f"{task:14s} {len(results):4d} {done:4d} {done / len(results):7.2f}  {bar}")
    total = sum(len(v) for v in per_task.values())
    done = sum(sum(v) for v in per_task.values())
    print(f"{'合计':14s} {total:4d} {done:4d} {done / total:7.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
