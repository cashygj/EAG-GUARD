#!/usr/bin/env python
"""对比两臂，列出"守卫弄坏"的对，并打印该对的拦截原因。

    python tools/diff_arms.py <基线目录> <守卫目录>
"""

from __future__ import annotations

import json
import sys
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
    base = load(Path(sys.argv[1]))
    guard = load(Path(sys.argv[2]))

    broken = [k for k in guard if k in base and base[k]["utility"] and not guard[k]["utility"]]
    print(f"守卫弄坏 {len(broken)} 对\n")
    for key in sorted(broken):
        data = guard[key]
        print(f"== {key[0]} × {key[1]}")
        steps = (data.get("guard") or {}).get("steps") or []
        denied = [s for s in steps if not s["allowed"]]
        if not denied:
            print("   无拦截（模型自身没做完，或输出审核裁掉了答案）")
        for step in denied:
            print(f"   [拦] {step['action'][:100]}")
            for reason in step["reasons"][:2]:
                print(f"        {reason[:170]}")
        print(f"   共 {len(steps)} 步，拦截 {len(denied)} 次")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
