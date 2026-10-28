import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.task_suite.load_suites import get_suite
from eag_guard.bench.agentdojo_runner import build_attack

suite = get_suite("v1", "banking")
user = suite.get_user_task_by_id("user_task_0")
inj = suite.get_injection_task_by_id("injection_task_3")
from types import SimpleNamespace
attack = build_attack("important_instructions", suite,
                      SimpleNamespace(name="qwen-plus"), model_label="qwen-plus")
injections = attack.attack(user, inj)
for key, value in injections.items():
    print(f"=== 注入点 {key} ===")
    print(value[:400])
    print()
