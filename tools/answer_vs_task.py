"""失败样本的"任务 vs 答复"对照，用于定位答复内容类问题。"""

import json
import sys
from pathlib import Path

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.task_suite.load_suites import get_suite

run = Path(sys.argv[1])
domain = sys.argv[2]
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5

suite = get_suite("v1", domain)
shown = 0
for path in sorted(run.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error") or data["utility"]:
        continue
    if shown >= limit:
        break
    task = suite.get_user_task_by_id(data["user_task"])
    print("=" * 70)
    print(f"{path.name}  util={data['utility']}")
    print("【任务】", task.PROMPT.strip().replace("\n", " ")[:220])
    truth = getattr(task, "GROUND_TRUTH_OUTPUT", None)
    if truth:
        print("【期望包含】", repr(truth)[:160])
    print("【答复】", (data.get("final_answer") or "（空）")[:500].replace("\n", " "))
    shown += 1
