import json
from pathlib import Path

run = Path(r"D:\EAG-GUARD\results\runs\workspace_v5_eag")
for i in range(4):
    path = run / f"workspace_user_task_0_injection_task_{i}.json"
    if not path.exists():
        print(i, "缺失")
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    calls = [c["function"] for c in (data.get("executed") or [])]
    answer = (data.get("final_answer") or "")[:120].replace("\n", " ")
    print(f"inj{i}: util={data['utility']} 调用={calls}")
    print(f"      {answer}")
