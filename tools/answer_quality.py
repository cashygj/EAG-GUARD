"""统计"最终答复被守卫提示占据"的轨迹数。"""

import json
from pathlib import Path

for run in ("travel_na2_eag", "workspace_v3_eag", "slack_full_eag", "banking_v15_eag"):
    root = Path(r"D:\EAG-GUARD\results\runs") / run
    if not root.exists():
        continue
    total = bad = redacted = 0
    for path in root.glob("*.json"):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("error"):
            continue
        total += 1
        answer = data.get("final_answer") or ""
        if answer.startswith("【授权守卫拦截") or "【授权守卫拦截了一次工具调用】" in answer[:40]:
            bad += 1
        if "〔已移除外部内容〕" in answer:
            redacted += 1
    print(f"{run:18s} 共 {total:3d} 对 | 答复=守卫提示 {bad:2d} | 含已移除标记 {redacted:2d}")
