"""把失败任务的"模型最终答复"打出来，和任务要求对照。"""

import json
import sys
from pathlib import Path

run = Path(sys.argv[1])
task = sys.argv[2] if len(sys.argv) > 2 else None

for path in sorted(run.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if task and task not in path.name:
        continue
    print(f"===== {path.name}  utility={data['utility']}")
    answer = data.get("final_answer") or "（无记录）"
    print("【模型最终答复】")
    print(answer[:900])
    print("\n【执行过的调用】")
    for call in (data.get("executed") or [])[-8:]:
        print("  ", call["function"], str(call["args"])[:100])
    print()
    if task:
        break
