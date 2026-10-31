"""在指定的一批对上统计某 run 目录的 ASR / UA（同口径对比用，域自动识别）。"""

import json
import sys
from pathlib import Path

run = Path(sys.argv[1])
users = range(int(sys.argv[2]), int(sys.argv[3]) + 1)
injs = range(int(sys.argv[4]), int(sys.argv[5]) + 1)
prefix = "unknown"
for name in ("workspace", "banking", "travel", "slack"):
    if name in run.name:
        prefix = name
        break

utilities = attacks = total = 0
for user in users:
    for inj in injs:
        path = run / f"{prefix}_user_task_{user}_injection_task_{inj}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("error"):
            continue
        total += 1
        utilities += bool(data["utility"])
        attacks += bool(data["security"])

if not total:
    print(f"{run.name}: 没有匹配的对（前缀推断为 {prefix}）")
else:
    print(f"{run.name}: {total} 对  ASR {attacks/total*100:.2f}%  UA {utilities/total*100:.2f}%")


