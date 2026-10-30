"""看 banking user_task_12 的 landlord-notices.txt 在注入前后各是什么。"""

import sys
from types import SimpleNamespace

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.task_suite.load_suites import get_suite

from eag_guard.bench.agentdojo_runner import build_attack

suite = get_suite("v1", "banking")
user = suite.get_user_task_by_id("user_task_12")

clean = suite.load_and_inject_default_environment({})
print("=== 干净 ===")
print(str(clean.filesystem.files.get("landlord-notices.txt"))[:600])

attack = build_attack("important_instructions", suite,
                      SimpleNamespace(name="qwen-plus", model="qwen-plus"))
for inj_id in ("injection_task_5", "injection_task_7"):
    inj = suite.get_injection_task_by_id(inj_id)
    env = suite.load_and_inject_default_environment(attack.attack(user, inj))
    print(f"\n=== 注入 {inj_id} 后 ===")
    print(str(env.filesystem.files.get("landlord-notices.txt"))[:700])
