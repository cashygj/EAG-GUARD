"""按 user/injection 编号区间统计某个 run 的子集表现。"""

import json
import sys
from pathlib import Path

run = Path(sys.argv[1])
lo_u, hi_u, lo_i, hi_i = (int(x) for x in sys.argv[2:6])

u = a = n = 0
for path in run.glob("*_injection_task_*.json"):
    parts = path.stem.split("_")
    try:
        user_idx = parts.index("task")
        ut = int(parts[user_idx + 1])
        inj = int(parts[-1])
    except (ValueError, IndexError):
        continue
    if not (lo_u <= ut <= hi_u and lo_i <= inj <= hi_i):
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error"):
        continue
    n += 1
    u += bool(data["utility"])
    a += bool(data["security"])

if n:
    print(f"{run.name} [{lo_u}-{hi_u}]x[{lo_i}-{hi_i}]: "
          f"{n} 对  ASR {a/n*100:.2f}%  UA {u/n:.4f}")
else:
    print(f"{run.name}: 该区间没有结果")
