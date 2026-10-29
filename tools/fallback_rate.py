"""统计有多少轨迹的授权范围来自"解析失败退化为只读"。"""

import json
import sys
from pathlib import Path

for run_dir in sys.argv[1:]:
    run = Path(run_dir)
    total = fallback = 0
    samples = []
    for path in sorted(run.glob("*.json")):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("error"):
            continue
        total += 1
        scope = (data.get("guard") or {}).get("scope") or ""
        if "解析失败" in scope:
            fallback += 1
            if len(samples) < 2:
                samples.append((path.name, data["utility"]))
    print(f"{run.name}: {fallback}/{total} 条走了只读退化 ({fallback/max(total,1):.0%})")
    for name, utility in samples:
        print(f"   例：{name} utility={utility}")
