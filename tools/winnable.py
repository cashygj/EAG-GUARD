"""判断回归集里的失败对"是否本来可完成"——用无防御臂的同一对做对照。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RUNS = Path(r"D:\EAG-GUARD\results\runs")
MANIFEST = json.loads(Path(r"D:\EAG-GUARD\results\regression_set.json").read_text(encoding="utf-8"))

UNDEF = {
    "travel": "travel_full_undefended",
    "workspace": "workspace_full_undefended",
    "slack": "slack_full_undefended",
    "banking": "banking_full_undefended",
}


def outcome(run: Path, name: str) -> bool | None:
    path = run / name
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error"):
        return None
    return bool(data["utility"])


for domain, pairs in MANIFEST.items():
    reg = RUNS / f"reg_{domain}"
    undef = RUNS / UNDEF.get(domain, "")
    if not reg.exists():
        continue
    winnable = []
    impossible = []
    for pair in pairs:
        name = f"{domain}_{pair['user_task']}_{pair['injection_task']}.json"
        now = outcome(reg, name)
        if now is None or now:
            continue                        # 已通过或没跑
        base = outcome(undef, name) if undef.exists() else None
        (winnable if base else impossible).append(pair["user_task"] + "×" + pair["injection_task"])

    print(f"{domain}: 仍失败 {len(winnable) + len(impossible)} 对")
    print(f"   可修（无防御能过）：{len(winnable)}  {winnable}")
    print(f"   注入导致无解（无防御也过不了）：{len(impossible)}  {impossible}")
