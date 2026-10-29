import json
from pathlib import Path

run = Path(r"D:\EAG-GUARD\results\runs\travel_na2_eag")
for task in ("user_task_4", "user_task_8"):
    data = json.loads((run / f"travel_{task}_injection_task_0.json").read_text(encoding="utf-8"))
    print(f"== {task} util={data['utility']}")
    for call in data.get("executed") or []:
        if call["function"] == "create_calendar_event":
            print("   create_calendar_event 参数:", json.dumps(call["args"], ensure_ascii=False)[:300])
    print("   答复:", (data.get("final_answer") or "")[:200].replace("\n", " "))
    print()
