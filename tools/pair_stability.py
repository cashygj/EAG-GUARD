#!/usr/bin/env python
"""跨多次重复，统计每一对的稳定性：全挂 / 全过 / 抖动。

    python tools/pair_stability.py results/runs/audit1_slack results/runs/audit2_slack results/runs/audit3_slack
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


def load(run_dir: Path) -> dict[tuple[str, str], dict]:
    out = {}
    for path in sorted(run_dir.glob("*.json")):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("error"):
            continue
        out[(data["user_task"], data["injection_task"])] = data
    return out


def main() -> int:
    runs = [load(Path(p)) for p in sys.argv[1:]]
    keys = sorted(set().union(*[set(r) for r in runs]))

    always_fail, always_pass, flaky = [], [], []
    for key in keys:
        outcomes = [bool(r[key]["utility"]) for r in runs if key in r]
        if all(outcomes):
            always_pass.append(key)
        elif not any(outcomes):
            always_fail.append(key)
        else:
            flaky.append((key, outcomes))

    print(f"对总数 {len(keys)}   全过 {len(always_pass)}   全挂 {len(always_fail)}   抖动 {len(flaky)}\n")
    if always_fail:
        print("== 三次全挂（系统性失败，值得修）")
        for key in always_fail:
            data = next(r[key] for r in runs if key in r)
            steps = (data.get("guard") or {}).get("steps") or []
            denied = [s for s in steps if not s["allowed"]]
            tools = sorted({s["action"].split("(")[0] for s in denied})
            print(f"  {key[0]} × {key[1]}：{len(steps)} 步，拦截 {len(denied)} 次"
                  + (f"（{', '.join(tools)}）" if tools else "（无拦截）"))
    if flaky:
        print("\n== 抖动（同一配置下结果不一致）")
        for key, outcomes in flaky:
            print(f"  {key[0]} × {key[1]}：{['过' if o else '挂' for o in outcomes]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
