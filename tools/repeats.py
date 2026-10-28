#!/usr/bin/env python
"""把同一配置的多次重复运行合成均值 ± 标准差。

    python tools/repeats.py results/runs/rep1 results/runs/rep2 results/runs/rep3

每一项都按"先算单次、再跨次平均"处理，避免把不同规模的分母混在一起。
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path


def load(run_dir: Path) -> tuple[int, float, float] | None:
    rows = []
    for path in sorted(run_dir.glob("*.json")):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("error"):
            continue
        rows.append(data)
    if not rows:
        return None
    n = len(rows)
    return n, sum(1 for r in rows if r["security"]) / n, sum(1 for r in rows if r["utility"]) / n


def main() -> int:
    dirs = [Path(p) for p in sys.argv[1:]]
    asrs, uas = [], []
    print(f"{'运行':30s} {'对数':>4s} {'ASR':>8s} {'UA':>8s}")
    for directory in dirs:
        result = load(directory)
        if result is None:
            print(f"{directory.name:30s}   （空）")
            continue
        n, asr, ua = result
        asrs.append(asr)
        uas.append(ua)
        print(f"{directory.name:30s} {n:4d} {asr * 100:7.2f}% {ua:8.4f}")
    if len(asrs) >= 2:
        print("-" * 54)
        print(f"{'均值':30s} {'':>4s} {statistics.mean(asrs) * 100:7.2f}% "
              f"{statistics.mean(uas):8.4f}")
        print(f"{'标准差':30s} {'':>4s} {statistics.stdev(asrs) * 100:7.2f}% "
              f"{statistics.stdev(uas):8.4f}")
        print(f"{'极差':30s} {'':>4s} "
              f"{(max(asrs) - min(asrs)) * 100:7.2f}% {max(uas) - min(uas):8.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
