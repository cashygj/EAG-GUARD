import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.functions_runtime import FunctionsRuntime
from agentdojo.task_suite.load_suites import get_suite

suite = get_suite("v1", "slack")
env = suite.load_and_inject_default_environment({})
runtime = FunctionsRuntime(suite.tools)

print("channels:", list(env.slack.channels))
print("users:", [getattr(u, "name", u) for u in env.slack.users])

for args in ({"channel": "External_", "user": "Charlie"},
             {"channel": "External", "user": "Charlie"}):
    result, error = runtime.run_function(env, "add_user_to_channel", args)
    print(args, "->", repr(result)[:120], "| error:", error)
