"""按域汇总失败原因，用于制定分域策略。

    python tools/domain_failures.py results/runs/policy_workspace ...
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path


def classify(reason: str) -> str:
    text = reason.lower()
    if "不在授权范围 t" in text:
        return "工具不在 T"
    if "不在授权范围 o" in text:
        return "对象不在 O"
    if "仿冒" in text:
        return "仿冒域名"
    if "只出现在不可信内容" in text or "未被委托" in text:
        return "链接未委托"
    if "不能归因" in text or "not specified" in text or "not delegated" in text \
            or "not attributable" in text or "is not user" in text:
        return "裁判判来源不明"
    if "金额" in text or "收款人" in text:
        return "金额/收款人越权"
    if "策略" in text:
        return "策略冲突"
    return "其它"


def main() -> int:
    for arg in sys.argv[1:]:
        run_dir = Path(arg)
        buckets: Counter[str] = Counter()
        samples: dict[str, str] = {}
        zero = 0
        total = 0
        for path in sorted(run_dir.glob("*.json")):
            if path.name == "summary.json":
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("error"):
                continue
            total += 1
            steps = (data.get("guard") or {}).get("steps") or []
            denied = [s for s in steps if not s["allowed"]]
            if data["utility"]:
                continue
            if not denied:
                zero += 1
                continue
            for step in denied:
                if step["reasons"]:
                    key = classify(step["reasons"][0])
                    buckets[key] += 1
                    samples.setdefault(key, step["reasons"][0][:110])
        print(f"===== {run_dir.name}（{total} 对，零拦截失败 {zero}）=====")
        for key, count in buckets.most_common():
            print(f"  {key:14s} {count:3d} 例 | 例：{samples[key]}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
