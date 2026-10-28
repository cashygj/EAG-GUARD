"""看"被拦之后模型做了什么"——这是恢复问题的直接证据。

    python tools/after_denial.py results/runs/travel_slice_eag
"""

import json
import sys
from pathlib import Path

run_dir = Path(sys.argv[1])
shown = 0
for path in sorted(run_dir.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error") or data["utility"]:
        continue
    steps = (data.get("guard") or {}).get("steps") or []
    denied = [s for s in steps if not s["allowed"]]
    if not denied:
        continue
    print(f"== {path.name}")
    print(f"   共 {len(steps)} 步，拦截 {len(denied)} 次")
    for s in steps:
        mark = "拦" if not s["allowed"] else "放"
        print(f"   [{mark}] {s['action'][:85]}")
    print(f"   实际执行：{[c['function'] for c in (data.get('executed') or [])]}")
    print()
    shown += 1
    if shown >= 3:
        break
