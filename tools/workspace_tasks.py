import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.task_suite.load_suites import get_suite

suite = get_suite("v1", "workspace")
for tid in ["user_task_0", "user_task_1", "user_task_2", "user_task_3", "user_task_4"]:
    task = suite.get_user_task_by_id(tid)
    truth = getattr(task, "GROUND_TRUTH_OUTPUT", None)
    print(f"--- {tid}")
    print("  请求:", task.PROMPT.strip()[:120].replace("\n", " "))
    print("  期望:", repr(truth)[:140])
