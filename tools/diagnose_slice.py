#!/usr/bin/env python
"""把一次跑批的"效用 / 步数 / 拦截"摆在一起看，判断效用损失是误杀还是预算耗尽。

    python tools/diagnose_slice.py results/runs/workspace_eag_slice25_v4
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def main() -> int:
    run_dir = Path(sys.argv[1])
    rows = []
    for path in sorted(run_dir.glob("*.json")):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        steps = (data.get("guard") or {}).get("steps") or []
        denied = [s for s in steps if not s["allowed"]]
        tools = sorted({s["action"].split("(")[0] for s in denied})
        rows.append({
            "pair": f"{data['user_task'][-1]}x{data['injection_task'][-1]}",
            "util": data["utility"],
            "steps": len(steps),
            "denied": len(denied),
            "tools": ",".join(tools),
            "err": bool(data["error"]),
        })

    print(f"{'pair':6s} {'util':5s} {'steps':5s} {'denied':6s} 被拦工具")
    for r in rows:
        print(f"{r['pair']:6s} {str(r['util']):5s} {r['steps']:<5d} {r['denied']:<6d} {r['tools']}")

    ok = [r for r in rows if r["util"]]
    bad = [r for r in rows if not r["util"]]
    print(f"\n完成 {len(ok)} / {len(rows)}")
    print(f"完成的平均步数 {sum(r['steps'] for r in ok) / max(len(ok), 1):.1f}，"
          f"未完成 {sum(r['steps'] for r in bad) / max(len(bad), 1):.1f}")
    print("未完成的对里，最后一步是拦截的比例：",
          f"{sum(1 for r in bad if r['denied'] >= r['steps']) }/{len(bad)}")
    print("步数分布：", Counter(r["steps"] for r in rows).most_common())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
