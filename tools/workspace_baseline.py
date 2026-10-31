"""workspace 守卫臂里"零拦截"的失败 = 模型侧失败，逐条看任务/期望/答复。"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.task_suite.load_suites import get_suite

run = Path(r"D:\EAG-GUARD\results\runs\final_workspace")
suite = get_suite("v1", "workspace")


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


buckets = Counter()
samples: dict[str, list[str]] = {}
for path in sorted(run.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error") or data["utility"]:
        continue
    steps = (data.get("guard") or {}).get("steps") or []
    if any(not s["allowed"] for s in steps):
        continue                       # 只看零拦截的
    answer = (data.get("final_answer") or "").strip()
    task = suite.get_user_task_by_id(data["user_task"])
    truth = str(getattr(task, "GROUND_TRUTH_OUTPUT", "") or "")

    if not answer:
        key = "答复为空"
    elif re.search(r"unable to|cannot access|don'?t have (?:permission|access)|没有权限|无法访问|无法直接",
                   answer, re.I):
        key = "自称无权限/无法访问"
    elif re.search(r"would you like|shall i|please confirm|是否希望|要不要|请确认",
                   answer, re.I):
        key = "反问用户（没执行）"
    elif truth and norm(truth)[:30] and norm(truth)[:30] in norm(answer):
        key = "答复含期望值但判失败"
    elif truth:
        key = "答复缺期望值"
    else:
        key = "无标准答案（动作类）"
    buckets[key] += 1
    samples.setdefault(key, []).append(
        f"{path.name.replace('workspace_','').replace('.json','')} | "
        f"任务：{task.PROMPT.strip().replace(chr(10),' ')[:70]} | "
        f"答复：{answer[:90].replace(chr(10),' ')}")

total = sum(buckets.values())
print(f"workspace 零拦截失败：{total} 对")
for key, value in buckets.most_common():
    print(f"  {key}: {value} ({value/total:.0%})")
    for line in samples[key][:2]:
        print(f"      {line}")
