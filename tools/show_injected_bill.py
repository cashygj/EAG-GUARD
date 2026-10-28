import sys
from types import SimpleNamespace

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.functions_runtime import FunctionsRuntime
from agentdojo.task_suite.load_suites import get_suite
from eag_guard.bench.agentdojo_runner import build_attack

suite = get_suite("v1", "banking")
user = suite.get_user_task_by_id("user_task_0")
attack = build_attack("important_instructions", suite,
                      SimpleNamespace(name="qwen-plus"), model_label="qwen-plus")

for inj_id in ("injection_task_0", "injection_task_3"):
    inj = suite.get_injection_task_by_id(inj_id)
    injections = attack.attack(user, inj)
    env = suite.load_and_inject_default_environment(injections)
    runtime = FunctionsRuntime(suite.tools)
    content, _ = runtime.run_function(env, "read_file",
                                      {"file_path": "bill-december-2023.txt"})
    print(f"===== {inj_id}: 注入后的账单（前 700 字）")
    print(content[:700])
    print()
