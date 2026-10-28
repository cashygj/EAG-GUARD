"""逐对比较两臂：找出「无防御能过、EAG 却失败」的样本——这全是守卫的代价。

    python tools/guard_cost.py results/runs/snap105v5_eag results/runs/snap_slack105_undef
"""

import json
import sys
from pathlib import Path


def load(run_dir: Path) -> dict[str, dict]:
    out = {}
    for path in run_dir.glob("*.json"):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("error"):
            continue
        out[path.name] = data
    return out


def main() -> int:
    eag = load(Path(sys.argv[1]))
    base = load(Path(sys.argv[2]))
    common = sorted(set(eag) & set(base))

    lost = [k for k in common if base[k]["utility"] and not eag[k]["utility"]]
    gained = [k for k in common if not base[k]["utility"] and eag[k]["utility"]]

    print(f"共同对数 {len(common)}")
    print(f"无防御过、EAG 挂：{len(lost)}（守卫的代价）")
    print(f"无防御挂、EAG 过：{len(gained)}")

    from collections import Counter

    by_task = Counter(k.split("_injection_")[0] for k in lost)
    print("\n按任务统计被守卫弄挂的对数：")
    for task, count in sorted(by_task.items(), key=lambda kv: -kv[1]):
        print(f"  {task}: {count}")

    print("\n具体样本（前 12）：")
    for name in lost[:12]:
        steps = (eag[name].get("guard") or {}).get("steps") or []
        denied = [s for s in steps if not s["allowed"]]
        reason = denied[0]["reasons"][0][:90] if denied and denied[0]["reasons"] else ""
        print(f"  {name}: 拦 {len(denied)} 次 | {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
