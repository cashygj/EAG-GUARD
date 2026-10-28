import json
import sys
from collections import Counter
from pathlib import Path

run_dir = Path(sys.argv[1])
steps_hist = Counter()
for path in sorted(run_dir.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error") or data["utility"]:
        continue
    steps = (data.get("guard") or {}).get("steps") or []
    if any(not s["allowed"] for s in steps):
        continue
    steps_hist[len(steps)] += 1

print("零拦截失败的步数分布：")
for n, count in sorted(steps_hist.items()):
    print(f"  {n:2d} 步：{count} 对")
