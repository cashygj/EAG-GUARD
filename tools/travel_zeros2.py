import json
from pathlib import Path

run = Path(r"D:\EAG-GUARD\results\runs\travel_na_eag")
for task in ("user_task_4", "user_task_8", "user_task_12", "user_task_17"):
    path = run / f"travel_{task}_injection_task_0.json"
    if not path.exists():
        print(task, "缺失")
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    calls = [c["function"] for c in (data.get("executed") or [])]
    print(f"== {task} util={data['utility']}")
    print("   调用:", calls)
    steps = (data.get("guard") or {}).get("steps") or []
    for step in steps:
        if not step["allowed"]:
            reason = step["reasons"][0] if step["reasons"] else ""
            print("   拦:", step["action"][:70], "|", reason[:70])
    answer = (data.get("final_answer") or "")[:300].replace("\n", " ")
    print("   答复:", answer)
    print()
