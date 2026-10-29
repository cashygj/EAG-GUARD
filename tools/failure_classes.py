"""把失败按"答复里有没有期望值 / 有没有相关调用"自动分类。

    python tools/failure_classes.py results/runs/workspace_v5_eag workspace
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.task_suite.load_suites import get_suite


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


def main() -> int:
    run = Path(sys.argv[1])
    domain = sys.argv[2]
    suite = get_suite("v1", domain)

    buckets: Counter[str] = Counter()
    examples: dict[str, list[str]] = {}
    for path in sorted(run.glob("*.json")):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("error") or data["utility"]:
            continue
        task = suite.get_user_task_by_id(data["user_task"])
        truth = str(getattr(task, "GROUND_TRUTH_OUTPUT", "") or "")
        answer = data.get("final_answer") or ""
        calls = data.get("executed") or []

        if "【授权守卫拦截" in answer[:60]:
            key = "答复是守卫提示（循环提前结束）"
        elif not answer.strip():
            key = "答复为空"
        elif not calls:
            key = "一次工具都没调"
        elif truth and norm(truth)[:40] and norm(truth)[:40] in norm(answer):
            key = "答复含期望值但仍判失败（副作用/格式问题）"
        elif truth and not any(norm(part) in norm(answer)
                               for part in str(truth).split() if len(part) > 3):
            key = "答复缺期望值（答案不对）"
        elif truth:
            key = "答复含部分期望值"
        else:
            key = "无标准答案可比对"
        buckets[key] += 1
        examples.setdefault(key, []).append(path.name.replace(".json", ""))

    total = sum(buckets.values())
    print(f"{domain}: 失败 {total} 对")
    for key, value in buckets.most_common():
        print(f"  {key}: {value}  ({value/total:.0%})")
        for name in examples[key][:2]:
            print(f"      例：{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
