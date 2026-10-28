#!/usr/bin/env python
"""列出某个运行目录里失败的样本及其拦截原因。

    python tools/failures.py results/runs/untf1_slack
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    run_dir = Path(sys.argv[1])
    for path in sorted(run_dir.glob("*.json")):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("utility"):
            continue
        steps = (data.get("guard") or {}).get("steps") or []
        denied = [s for s in steps if not s["allowed"]]
        print(f"== {data['user_task']} x {data['injection_task']}: "
              f"{len(steps)} 步，拦截 {len(denied)} 次")
        for step in denied[:3]:
            print(f"   [拦] {step['action'][:75]}")
            reason = step["reasons"][0] if step["reasons"] else ""
            print(f"        {reason[:150]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
