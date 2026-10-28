import json
from pathlib import Path

run = Path(r"D:\EAG-GUARD\results\runs\banking_act2_eag")
hits = 0
shown = 0
for path in sorted(run.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    text = json.dumps(data, ensure_ascii=False)
    if "正确的取值" in text:
        hits += 1
        if shown < 2:
            print(f"== {path.name} util={data['utility']}")
            shown += 1
print(f"\n包含「正确的取值」的轨迹：{hits}")
