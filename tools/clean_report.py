#!/usr/bin/env python
"""看一次干净基线里，哪些任务失败、以及失败是否由拦截造成。

    python tools/clean_report.py results/runs/clean_eag_nocache
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    run_dir = Path(sys.argv[1])
    for path in sorted(run_dir.glob("*_clean.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        steps = (data.get("guard") or {}).get("steps") or []
        denied = [s for s in steps if not s["allowed"]]
        print(f"{data['user_task']}: util={data['utility']} "
              f"steps={len(steps)} denied={len(denied)}")
        for step in denied:
            print(f"    拦: {step['action'][:80]}")
            print(f"       {'；'.join(step['reasons'])[:180]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
