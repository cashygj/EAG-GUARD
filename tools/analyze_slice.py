#!/usr/bin/env python
"""分析一次跑批的轨迹：统计拦截原因，定位是哪一类误杀。

    python tools/analyze_slice.py results/runs/workspace_eag_slice25
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def classify(reason: str) -> str:
    if "不在授权范围 T" in reason or "未注册" in reason:
        return "工具未授权"
    if "不在授权范围 O" in reason:
        return "对象未授权"
    if "只可溯源到不可信内容" in reason:
        return "参数来自不可信内容"
    if "无法归因" in reason:
        return "参数无法归因"
    if "只读策略" in reason:
        return "只读策略"
    if "裁判" in reason or "越权" in reason:
        return "裁判拒绝"
    return "其他"


def main() -> int:
    run_dir = Path(sys.argv[1])
    files = sorted(p for p in run_dir.glob("*.json") if p.name != "summary.json")
    print(f"{len(files)} 对\n")

    utility = 0
    categories: Counter[str] = Counter()
    denied_tools: Counter[str] = Counter()
    pairs_with_denial = 0
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        utility += int(data["utility"])
        steps = (data.get("guard") or {}).get("steps") or []
        denied = [s for s in steps if not s["allowed"]]
        if denied:
            pairs_with_denial += 1
        for step in denied:
            tool = step["action"].split("(")[0]
            denied_tools[tool] += 1
            for reason in step["reasons"]:
                categories[classify(reason)] += 1

    print(f"UA = {utility}/{len(files)} = {utility / max(len(files), 1):.2f}")
    print(f"有拦截的对：{pairs_with_denial}/{len(files)}")
    print("\n拦截原因：")
    for name, count in categories.most_common():
        print(f"  {name:14s} {count}")
    print("\n被拦最多的工具：")
    for name, count in denied_tools.most_common(8):
        print(f"  {name:26s} {count}")

    print("\n逐对：")
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        steps = (data.get("guard") or {}).get("steps") or []
        denied = [s["action"].split("(")[0] for s in steps if not s["allowed"]]
        mark = "完成" if data["utility"] else "未完成"
        print(f"  {data['user_task']} × {data['injection_task']}: {mark}"
              + (f"  拦了 {', '.join(denied)}" if denied else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
