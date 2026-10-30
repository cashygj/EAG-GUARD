"""列出回归集里仍失败的对，附任务原文、期望值、调用、答复、拦截原因。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.task_suite.load_suites import get_suite

RUNS = Path(r"D:\EAG-GUARD\results\runs")
MANIFEST = json.loads(Path(r"D:\EAG-GUARD\results\regression_set.json").read_text(encoding="utf-8"))

for domain, pairs in MANIFEST.items():
    run = RUNS / f"reg_{domain}"
    if not run.exists():
        print(f"{domain}: 还没有回归跑批结果")
        continue
    suite = get_suite("v1", domain)
    print("#" * 72)
    print(f"## {domain}")
    for pair in pairs:
        path = run / f"{domain}_{pair['user_task']}_{pair['injection_task']}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["utility"]:
            continue
        task = suite.get_user_task_by_id(pair["user_task"])
        print("=" * 72)
        print(f"{pair['user_task']} × {pair['injection_task']}")
        print("【任务】", task.PROMPT.strip().replace(chr(10), " ")[:200])
        truth = getattr(task, "GROUND_TRUTH_OUTPUT", None)
        if truth:
            print("【期望】", repr(truth)[:200])
        calls = [c["function"] for c in (data.get("executed") or [])]
        print("【调用】", calls[:10])
        steps = (data.get("guard") or {}).get("steps") or []
        denials = [s for s in steps if not s["allowed"]]
        for step in denials[:2]:
            reason = step["reasons"][0] if step["reasons"] else ""
            print("【拦截】", step["action"][:60], "|", reason[:90])
        print("【答复】", (data.get("final_answer") or "（空）")[:300].replace(chr(10), " "))
