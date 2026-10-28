import json
import sys
from pathlib import Path

run_dir = Path(sys.argv[1])
task_prefix = sys.argv[2]
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 2

shown = 0
for path in sorted(run_dir.glob(f"*{task_prefix}*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if not path.name.startswith(task_prefix) and task_prefix not in path.name:
        continue
    print(f"== {path.name}  util={data.get('utility')}")
    for call in data.get("executed") or []:
        print("   执行:", call["function"], str(call["args"])[:110])
    shown += 1
    if shown >= limit:
        break
