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
    if any(not s["allowed"] for s in steps):
        continue
    print(f"== {path.name}")
    for s in steps:
        print("   放行:", s["action"][:90])
    for c in data.get("executed") or []:
        print("   执行:", c["function"], str(c["args"])[:70])
    shown += 1
    if shown >= 4:
        break
