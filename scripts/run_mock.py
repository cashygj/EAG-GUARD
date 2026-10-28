#!/usr/bin/env python
"""跑离线 mock 基准，打印与报告表 4-1/4-2 同形的结果。

用法：
    python scripts/run_mock.py
    python scripts/run_mock.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eag_guard.bench.runner import ARMS, run_all  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, help="把完整结果写到 JSON")
    args = parser.parse_args()

    results = run_all()
    payload = {}
    for arm, (summary, traces) in results.items():
        print(f"\n=== {arm} ===")
        header = ["域", "对数", "ASR", "UA", "工具级ASR"]
        rows = summary.as_table()
        widths = [max(len(str(r[k])) for r in rows + [dict(zip(header, header))])
                  for k in header]
        print("  ".join(h.ljust(w) for h, w in zip(header, widths)))
        print("  ".join("-" * w for w in widths))
        for row in rows:
            print("  ".join(str(row[k]).ljust(w) for k, w in zip(header, widths)))
        payload[arm] = {
            "summary": [dict(r) for r in rows],
            "traces": [t.to_dict() for t in traces],
        }

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        print(f"\n写到 {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
