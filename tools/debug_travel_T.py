import json
import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.task_suite.load_suites import get_suite
from eag_guard.bench.agentdojo_runner import toolspecs_from_suite
from eag_guard.parsing import tools_implied_by_request

trace = json.load(open(
    r"D:\EAG-GUARD\results\runs\travel_v3_eag\travel_user_task_10_injection_task_0.json",
    encoding="utf-8"))
request = trace["guard"]["request"]
print("请求全文：")
print(request)
print()

suite = get_suite("v1", "travel")
specs = toolspecs_from_suite(suite)
specs = list(specs.values()) if isinstance(specs, dict) else list(specs)
print("reserve_restaurant 在规格里:", any(s.name == "reserve_restaurant" for s in specs))
print("兜底推导:", sorted(tools_implied_by_request(request, specs)))
print("轨迹 T 含 reserve:", "reserve" in trace["guard"]["scope"])
