"""重建回归集：只收"无防御能过、加了守卫却挂"的对——这些才是我们该修的。"""

from __future__ import annotations

import json
from pathlib import Path

RUNS = Path(r"D:\EAG-GUARD\results\runs")
OUT = Path(r"D:\EAG-GUARD\results\regression_set.json")

# (守卫臂, 无防御臂)
PAIRS = {
    "travel": ("travel_rv_eag", "travel_full_undefended"),
    "workspace": ("workspace_v6_eag", "workspace_full_undefended"),
    "slack": ("slack_full_eag", "slack_full_undefended"),
    "banking": ("banking_v15_eag", "banking_full_undefended"),
}
# 已知"效用与安全互斥"的对（见 docs/28-基准缺陷.md），不进回归集
EXCLUDE = {
    ("banking", "user_task_15", "injection_task_1"),
}

PER_DOMAIN_LOSS = 8      # 守卫净损失样本
PER_DOMAIN_CONTROL = 3   # 对照样本（两边都过）


def load(run: Path) -> dict[str, dict]:
    out = {}
    for path in run.glob("*.json"):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("error"):
            continue
        out[path.name] = data
    return out


def main() -> int:
    manifest = {}
    for domain, (guard_name, undef_name) in PAIRS.items():
        guard_run, undef_run = RUNS / guard_name, RUNS / undef_name
        if not guard_run.exists() or not undef_run.exists():
            print(f"{domain}: 缺少跑批（{guard_name} / {undef_name}）")
            continue
        guard, undef = load(guard_run), load(undef_run)
        loss, control = [], []
        for name, data in sorted(guard.items()):
            other = undef.get(name)
            if other is None:
                continue
            entry = {"user_task": data["user_task"],
                     "injection_task": data["injection_task"]}
            if (domain, data["user_task"], data["injection_task"]) in EXCLUDE:
                continue
            if other["utility"] and not data["utility"]:
                loss.append(entry)
            elif other["utility"] and data["utility"]:
                control.append(entry)
        picked = loss[:PER_DOMAIN_LOSS] + control[:PER_DOMAIN_CONTROL]
        if picked:
            manifest[domain] = picked
        print(f"{domain}: 净损失 {len(loss)} 对，取 {min(len(loss), PER_DOMAIN_LOSS)}；"
              f"对照取 {min(len(control), PER_DOMAIN_CONTROL)}")

    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(v) for v in manifest.values())
    print(f"\n已写入 {OUT}（共 {total} 对，约 {max(1, total * 15 // 60)} 分钟一轮）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

