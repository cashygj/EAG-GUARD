#!/usr/bin/env python
"""把一批运行目录汇总成与报告表 4-1 同形的结果表（按对 + 等权）。

    python tools/report_bench.py results/runs/full629b_*

每个目录名形如 `<域>_<臂>...`，域取第一个下划线前的部分。
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

DOMAINS = ["workspace", "slack", "travel", "banking"]


def load(run_dir: Path) -> list[dict]:
    rows = []
    for path in sorted(run_dir.glob("*.json")):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("error"):
            continue
        rows.append(data)
    return rows


def main() -> int:
    dirs = [Path(p) for p in sys.argv[1:]]
    if not dirs:
        print("用法：python tools/report_bench.py <运行目录>...")
        return 2

    per_domain: dict[str, list[dict]] = defaultdict(list)
    for directory in dirs:
        rows = load(directory)
        if not rows:
            continue
        # 目录名里任意位置出现的域名都算，例如 loop_eag_slack → slack
        domain = next((d for d in DOMAINS if d in directory.name.split("_")),
                      directory.name.split("_")[0])
        per_domain[domain].extend(rows)

    print(f"{'域':10s} {'对数':>5s} {'ASR':>8s} {'UA':>8s}")
    print("-" * 36)
    total_n = total_atk = total_ok = 0
    asrs, uas = [], []
    for domain in DOMAINS:
        rows = per_domain.get(domain)
        if not rows:
            continue
        n = len(rows)
        atk = sum(1 for r in rows if r["security"])
        ok = sum(1 for r in rows if r["utility"])
        total_n += n
        total_atk += atk
        total_ok += ok
        asr, ua = atk / n, ok / n
        asrs.append(asr)
        uas.append(ua)
        print(f"{domain:10s} {n:5d} {asr * 100:7.2f}% {ua:8.4f}")
    print("-" * 36)
    if total_n:
        print(f"{'合计(按对)':10s} {total_n:5d} {total_atk / total_n * 100:7.2f}% "
              f"{total_ok / total_n:8.4f}")
    if asrs:
        print(f"{'合计(等权)':10s} {'—':>5s} {sum(asrs) / len(asrs) * 100:7.2f}% "
              f"{sum(uas) / len(uas):8.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
