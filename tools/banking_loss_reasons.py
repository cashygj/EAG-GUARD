"""banking：守卫净损失对的拦截理由聚类（多守卫样本合并）。"""

import json
from collections import Counter
from pathlib import Path

RUNS = Path(r"D:\EAG-GUARD\results\runs")
GUARD_RUNS = ["q35_banking_full", "rep_bank_g2", "rep_bank_g3"]
UNDEF = RUNS / "rep_bank_undef"

undef = {}
for path in UNDEF.glob("banking_*.json"):
    data = json.loads(path.read_text(encoding="utf-8"))
    undef[path.name] = bool(data["utility"])

reasons = Counter()
examples = {}
for name in GUARD_RUNS:
    run = RUNS / name
    if not run.exists():
        continue
    for path in run.glob("banking_*.json"):
        parts = path.stem.split("_")
        try:
            user_index = parts.index("task")
            if int(parts[user_index + 1]) > 9 or int(parts[-1]) > 5:
                continue
        except (ValueError, IndexError):
            continue
        if not undef.get(path.name):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["utility"]:
            continue
        steps = (data.get("guard") or {}).get("steps") or []
        denials = [s for s in steps if not s["allowed"]]
        if not denials:
            reasons["（无拦截，模型侧）"] += 1
            continue
        for step in denials[:2]:
            text = (step["reasons"][0] if step["reasons"] else "无理由")[:34]
            kind = ("金额/参数无法归因" if "无法归因" in text or "只可溯源" in text
                    else "对象不在授权范围" if "不在授权范围" in text
                    else "裁判判定扩权" if "url" in text.lower() or "扩权" in text
                    else "其它")
            reasons[kind] += 1
            examples.setdefault(kind, f"{path.stem}: {text}")

print("守卫净损失的拦截理由分布（三个样本合并）：")
for kind, count in reasons.most_common():
    print(f"  {kind}: {count}")
    if kind in examples:
        print(f"      例：{examples[kind]}")
