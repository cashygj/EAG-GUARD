"""对一次运行做一致性检查：放行的动作必须真的被执行。

    python tools/audit_run.py results/runs/fix_59
"""

import json
import sys
from pathlib import Path


def main() -> int:
    run_dir = Path(sys.argv[1])
    problems = 0
    for path in sorted(run_dir.glob("*.json")):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        steps = (data.get("guard") or {}).get("steps") or []
        allowed = [s for s in steps if s["allowed"]]
        executed = data.get("executed") or []
        if len(allowed) != len(executed):
            problems += 1
            print(f"{path.name}: 放行 {len(allowed)} 条，执行 {len(executed)} 条")
            for s in allowed:
                print("   放行:", s["action"][:80])
            for c in executed:
                print("   执行:", c["function"], c["args"])
    print(f"\n不一致的轨迹：{problems}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
