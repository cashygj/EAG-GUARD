import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.functions_runtime import FunctionsRuntime
from agentdojo.task_suite.load_suites import get_suite

suite = get_suite("v1", "banking")
env = suite.load_and_inject_default_environment({})
runtime = FunctionsRuntime(suite.tools)

result, error = runtime.run_function(env, "get_most_recent_transactions", {"n": 3})
print("error:", error)
print(type(result))
print(repr(result)[:1200])
