import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.task_suite.load_suites import get_suite

suite = get_suite("v1", "slack")
for i in (0, 3, 4, 7, 8, 9, 10, 12, 15, 18):
    task = suite.get_user_task_by_id(f"user_task_{i}")
    print(f"--- user_task_{i}")
    print("   ", task.PROMPT.strip()[:170].replace("\n", " "))
