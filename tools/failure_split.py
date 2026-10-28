"""把失败拆成「守卫拦掉的」和「模型自己没做完的」。

    python tools/failure_split.py results/runs/snap105v5_eag
"""

import json
import sys
from collections import Counter
from pathlib import Path


def main() -> int:
    run_dir = Path(sys.argv[1])
    buckets: Counter[str] = Counter()
    denied_pairs = []
    for path in sorted(run_dir.glob("*.json")):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("error"):
            continue
        steps = (data.get("guard") or {}).get("steps") or []
        denied = [s for s in steps if not s["allowed"]]
        if data["utility"]:
            buckets["成功"] += 1
        elif denied:
            buckets["失败·被拦过"] += 1
            denied_pairs.append((path.name, len(steps), len(denied)))
        else:
            buckets["失败·零拦截"] += 1

    total = sum(buckets.values())
    for key, value in buckets.most_common():
        print(f"{key:12s} {value:3d}  ({value / total:.0%})")
    print(f"{'合计':12s} {total:3d}")
    print("\n被拦过的失败样本：")
    for name, steps, denied in denied_pairs[:10]:
        print(f"  {name}: {steps} 步，拦截 {denied} 次")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
