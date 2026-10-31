"""银行业守卫净损失对的行为画像：被拦之后模型还做了什么。"""

import json
from pathlib import Path

RUNS = Path(r"D:\EAG-GUARD\results\runs")
guard_run = RUNS / "final3_banking"
undef_run = RUNS / "banking_full_undefended"

lost = []
for path in sorted(guard_run.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["utility"]:
        continue
    base_path = undef_run / path.name
    if not base_path.exists():
        continue
    base = json.loads(base_path.read_text(encoding="utf-8"))
    if not base["utility"]:
        continue
    steps = (data.get("guard") or {}).get("steps") or []
    denials = [i for i, s in enumerate(steps) if not s["allowed"]]
    after = len(steps) - denials[0] - 1 if denials else None
    lost.append((path.name.replace("banking_", "").replace(".json", ""), after,
                 [s["action"][:40] for s in steps[denials[0]:denials[0] + 3]] if denials else []))

print(f"banking 守卫净损失：{len(lost)} 对")
for name, after, actions in lost:
    print(f"  {name}: 被拦后还做 {after} 步 | {actions}")
