"""检查哪些注入会改写频道名（使 external 频道不再存在）。"""

import sys
from types import SimpleNamespace

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.functions_runtime import FunctionsRuntime
from agentdojo.task_suite.load_suites import get_suite

import eag_guard.bench.agentdojo_runner as R

suite = get_suite("v1", "slack")
attack = R.build_attack(
    "important_instructions", suite,
    SimpleNamespace(name="Qwen/Qwen2.5-32B-Instruct", model="qwen-plus"),
)
runtime = FunctionsRuntime(suite.tools)

for task_id in ("user_task_7", "user_task_9", "user_task_10", "user_task_12"):
    user_task = suite.get_user_task_by_id(task_id)
    marks = []
    for index in range(1, 6):
        injection_task = suite.get_injection_task_by_id(f"injection_task_{index}")
        env = suite.load_and_inject_default_environment(
            attack.attack(user_task, injection_task)
        )
        channels, _ = runtime.run_function(env, "get_channels", {})
        poisoned = any("INFORMATION" in str(channel) for channel in channels)
        marks.append(f"inj{index}={'污染' if poisoned else '正常'}")
    print(f"{task_id}: " + "  ".join(marks))
