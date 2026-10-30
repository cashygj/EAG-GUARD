"""看我们自己的执行器如何把 get_day_calendar_events 的结果写回消息。"""

import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.functions_runtime import FunctionCall, FunctionsRuntime, TaskEnvironment
from agentdojo.task_suite.load_suites import get_suite

from eag_guard.bench.scaffold import format_tool_output, make_executor

suite = get_suite("v1", "workspace")
env = suite.load_and_inject_default_environment({})
runtime = FunctionsRuntime(suite.tools)

call = FunctionCall(function="get_day_calendar_events", args={"day": "2024-05-15"}, id="c1")
result, error = runtime.run_function(env, call.function, call.args)
print("原始返回类型:", type(result))
text = format_tool_output(result)
print("格式化后（前 400 字）:")
print(str(text)[:400])
print("error:", error)
