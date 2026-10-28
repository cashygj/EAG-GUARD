import inspect
import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.task_suite.load_suites import get_suite

suite = get_suite("v1", "banking")
for tid in ["user_task_0", "user_task_10", "user_task_12", "user_task_15"]:
    src = inspect.getsource(suite.get_user_task_by_id(tid).utility)
    uses_output = "model_output" in src.split(":", 2)[2] if src.count(":") > 2 else False
    print(f"=== {tid}  (用到 model_output: {uses_output})")
    for line in src.splitlines():
        if "model_output" in line or "len(" in line or "in model_output" in line:
            print("   ", line.strip()[:110])
    print()
