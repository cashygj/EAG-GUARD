#!/usr/bin/env python
"""挑出被攻破的对，把完整轨迹打出来。

    python tools/show_breach.py results/runs/slack_eag_slice25
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
        if not data["security"]:
            continue
        print(f"===== 被攻破：{data['user_task']} × {data['injection_task']} "
              f"(utility={data['utility']}) =====")
        print("执行的调用：")
        for call in data["executed"]:
            print(f"  {call['function']}({call['args']})")
        print("守卫步骤：")
        for step in (data.get("guard") or {}).get("steps", []):
            flag = "放行" if step["allowed"] else "拦截"
            print(f"  [{flag}] {step['action'][:110]}")
            print(f"         provenance={step['provenance']}")
            if step["reasons"]:
                for reason in step["reasons"]:
                    print(f"         ! {reason[:180]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
