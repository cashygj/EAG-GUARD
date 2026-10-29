import json
from pathlib import Path

run = Path(r"D:\EAG-GUARD\results\runs\travel_v2_eag")
shown = 0
for path in sorted(run.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error") or data["utility"]:
        continue
    calls = data.get("executed") or []
    if any(c["function"].startswith("reserve_") for c in calls):
        continue
    print(f"== {path.name}")
    for c in calls[-6:]:
        print("   ", c["function"], str(c["args"])[:80])
    steps = (data.get("guard") or {}).get("steps") or []
    denied = [s for s in steps if not s["allowed"]]
    print(f"   步数 {len(steps)}，拦截 {len(denied)}")
    for s in denied[:2]:
        print("     拦:", s["action"][:70], "|", (s["reasons"][0] if s["reasons"] else "")[:80])
    print()
    shown += 1
    if shown >= 3:
        break
