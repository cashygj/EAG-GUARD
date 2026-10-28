#!/usr/bin/env python
"""把多次跑批的结果合成一张对照表，并做逐对比较。

    python tools/compare_runs.py --arm 无防御 results/runs/slack_undefended_v2 \
                                 --arm EAG   results/runs/slack_eag_v6

每个 --arm 后跟一个运行目录；第一个当作基线做配对比较。
"""

from __future__ import annotations

import argparse
import json
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


def stats(runs: dict) -> tuple[int, int, int]:
    n = len(runs)
    attacked = sum(1 for r in runs.values() if r["security"])
    done = sum(1 for r in runs.values() if r["utility"])
    return n, attacked, done


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", nargs=2, action="append", metavar=("LABEL", "DIR"),
                    required=True)
    args = ap.parse_args()

    loaded = [(label, Path(directory), load(Path(directory))) for label, directory in args.arm]

    print(f"{'臂':10s} {'目录':34s} {'对数':>4s} {'ASR':>8s} {'UA':>7s}")
    for label, directory, runs in loaded:
        n, attacked, done = stats(runs)
        print(f"{label:10s} {str(directory.name):34s} {n:4d} "
              f"{attacked / n * 100:7.2f}% {done / n:7.4f}")

    if len(loaded) >= 2:
        base_label, _, base = loaded[0]
        for label, _, other in loaded[1:]:
            common = sorted(set(base) & set(other))
            if not common:
                continue
            fixed = sum(1 for k in common if base[k]["security"] and not other[k]["security"])
            broken = sum(1 for k in common if not base[k]["security"] and other[k]["security"])
            u_fixed = sum(1 for k in common if other[k]["utility"] and not base[k]["utility"])
            u_broken = sum(1 for k in common if base[k]["utility"] and not other[k]["utility"])
            print(f"\n{base_label} → {label}（共同 {len(common)} 对）")
            print(f"  安全：修好 {fixed} 对，弄坏 {broken} 对")
            print(f"  效用：修好 {u_fixed} 对，弄坏 {u_broken} 对")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
