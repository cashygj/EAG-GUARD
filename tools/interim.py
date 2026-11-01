"""对未跑完的目录做"已完成部分"的中间统计。"""

import json
import sys
from pathlib import Path

run = Path(sys.argv[1])
done = util = attack = 0
for path in run.glob("*.json"):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error"):
        continue
    done += 1
    util += bool(data["utility"])
    attack += bool(data["security"])

if done:
    print(f"{run.name}: 已完成 {done} 对 | 中间 ASR {attack/done*100:.2f}% | 中间 UA {util/done:.4f}")
else:
    print(f"{run.name}: 还没有结果")
