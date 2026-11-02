"""banking 在 qwen3.5-27b 下的"守卫净损失"：无防御过、守卫挂，看拦截理由。"""

import json
from pathlib import Path

RUNS = Path(r"D:\EAG-GUARD\results\runs")
guard_run = RUNS / "q35_banking_full"
undef_run = RUNS / "q35ub_banking30"

lost = []
for path in sorted(undef_run.glob("*.json")):
    if path.name == "summary.json":
        continue
    base = json.loads(path.read_text(encoding="utf-8"))
    if not base["utility"]:
        continue
    guard_path = guard_run / path.name
    if not guard_path.exists():
        continue
    data = json.loads(guard_path.read_text(encoding="utf-8"))
    if data["utility"]:
        continue
    steps = (data.get("guard") or {}).get("steps") or []
    denials = [s for s in steps if not s["allowed"]]
    lost.append((
        path.name.replace("banking_", "").replace(".json", ""),
        [(s["action"][:52], (s["reasons"][0] if s["reasons"] else "")[:80]) for s in denials],
        [c["function"] for c in (data.get("executed") or [])],
    ))

print(f"banking（qwen3.5-27b）守卫净损失：{len(lost)} 对")
for name, denials, calls in lost:
    print(f"\n== {name}")
    print("   执行:", calls)
    for action, reason in denials[:3]:
        print(f"   拦: {action} | {reason}")
