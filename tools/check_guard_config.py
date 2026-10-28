import sys
from types import SimpleNamespace

sys.path.insert(0, "D:/EAG-GUARD/src")
from eag_guard.bench.agentdojo_runner import make_guard
from eag_guard.pipeline import GuardConfig

suite = SimpleNamespace(name="banking", tools=[])
client = SimpleNamespace(model="x", complete=lambda *a, **k: "{}", api_key="k",
                         base_url="http://x", temperature=0.0)
guard_el = make_guard(suite, client)
print("config.read_policy   =", guard_el.guard.config.read_policy)
print("config.strict_params =", guard_el.guard.config.strict_params)
print("feedback             =", guard_el.feedback)
