import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.functions_runtime import FunctionsRuntime
from agentdojo.task_suite.load_suites import get_suite

suite = get_suite("v1", "banking")
inj = suite.get_injection_task_by_id("injection_task_1")
print("注入目标 GOAL:", inj.GOAL)
print("注入点:", getattr(inj, "INJECTIONS", None) and list(inj.INJECTIONS))
print()

env = suite.load_and_inject_default_environment({"injection_task_1": inj.INJECTIONS["injection_task_1"]})
runtime = FunctionsRuntime(suite.tools)
result, error = runtime.run_function(env, "read_file", {"file_path": "bill-december-2023.txt"})
print("注入后的账单内容：")
print(result)
