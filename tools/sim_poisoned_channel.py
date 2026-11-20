"""模拟：把用户加到"被注入污染的 External 频道"后，效用判定能不能通过。"""

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

for task_id, user in (("user_task_7", "Charlie"), ("user_task_9", "Alice"),
                      ("user_task_10", None)):
    task = suite.get_user_task_by_id(task_id)
    injection = suite.get_injection_task_by_id("injection_task_1")
    env = suite.load_and_inject_default_environment(attack.attack(task, injection))
    pre = env.model_copy(deep=True)

    channels, _ = runtime.run_function(env, "get_channels", {})
    external = [c for c in channels if str(c).startswith("External")]
    print(f"\n=== {task_id}")
    print("  污染后的外部频道名（前 40 字）:", repr(str(external[0])[:40]) if external else "无")

    if task_id == "user_task_7":
        targets = [user]
    elif task_id == "user_task_9":
        targets = [user]
    else:
        # task 10：把不在频道里的用户都加进去
        members, _ = runtime.run_function(env, "get_users_in_channel",
                                          {"channel": external[0]})
        targets = [u for u in ("Alice", "Bob", "Charlie", "Eve") if u not in (members or [])]

    for target in targets:
        result, error = runtime.run_function(
            env, "add_user_to_channel", {"channel": external[0], "user": target}
        )
        print(f"  加 {target} -> err={error}")

    utility = task.utility("", pre, env)
    print("  效用（用污染频道名操作）:", utility)
