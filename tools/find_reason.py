import json
import sys
from pathlib import Path

run_dir = Path(sys.argv[1])
needle = sys.argv[2]

for path in sorted(run_dir.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    for step in (data.get("guard") or {}).get("steps") or []:
        if step["allowed"]:
            continue
        for reason in step["reasons"]:
            if needle in reason:
                print(f"== {path.name}")
                print("  动作:", step["action"][:100])
                print("  理由:", reason[:220])
                print("  范围:", (data["guard"]["scope"] or "")[:600].replace("\n", "\n        "))
                raise SystemExit(0)
print("未找到")
