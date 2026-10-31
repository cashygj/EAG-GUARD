import json
from pathlib import Path

base = Path(r"D:\EAG-GUARD\results\runs\banking_full_undefended")
for inj in (0, 2, 3):
    path = base / f"banking_user_task_2_injection_task_{inj}.json"
    if not path.exists():
        print(inj, "缺失")
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    print(f"inj{inj}: 无防御 utility={data['utility']} security={data['security']}")
