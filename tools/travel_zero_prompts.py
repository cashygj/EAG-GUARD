import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.task_suite.load_suites import get_suite

suite = get_suite("v1", "travel")
zeros = [3, 4, 5, 7, 8, 9, 10, 11, 12, 15, 17, 19]
for i in zeros:
    task = suite.get_user_task_by_id(f"user_task_{i}")
    print(f"--- user_task_{i}（0 完成）")
    print("   ", task.PROMPT.strip().replace("\n", " ")[:240])
    print()
