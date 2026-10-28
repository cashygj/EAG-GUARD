import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.functions_runtime import FunctionsRuntime
from agentdojo.task_suite.load_suites import get_suite

suite = get_suite("v1", "banking")
env = suite.load_and_inject_default_environment({})
runtime = FunctionsRuntime(suite.tools)

result, error = runtime.run_function(env, "read_file", {"file_path": "bill-december-2023.txt"})
print("error:", error)
print(result[:800] if isinstance(result, str) else result)
