"""看某条失败轨迹里"解析器给出的 T"和"模型想做但被拦的工具"。

    python tools/scope_gap.py results/runs/status_travel travel_user_task_3 injection_task_1
"""

import json
import sys
from pathlib import Path

run_dir = Path(sys.argv[1])
prefix = sys.argv[2]
inj = sys.argv[3] if len(sys.argv) > 3 else "injection_task_1"

path = run_dir / f"{prefix}_{inj}.json"
data = json.loads(path.read_text(encoding="utf-8"))
print(f"== {path.name}  util={data['utility']}")
print("\n【请求】")
print(data["guard"]["request"][:300])
print("\n【解析出的授权范围】")
print(data["guard"]["scope"][:900])
print("\n【守卫步骤】")
for step in data["guard"]["steps"]:
    mark = "放" if step["allowed"] else "拦"
    print(f"  [{mark}] {step['action'][:90]}")
    for r in step["reasons"][:1]:
        print("        " + r[:120])
