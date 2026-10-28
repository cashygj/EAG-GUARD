import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from agentdojo.functions_runtime import FunctionsRuntime
from agentdojo.task_suite.load_suites import get_suite
from agentdojo.types import text_content_block_from_string

suite = get_suite("v1", "travel")
task = suite.get_user_task_by_id("user_task_0")
print("工具：", task.GROUND_TRUTH_OUTPUT if hasattr(task, "GROUND_TRUTH_OUTPUT") else "-")

env = suite.load_and_inject_default_environment({})
runtime = FunctionsRuntime(suite.tools)

# 先看酒店是否存在、评分多少
result, error = runtime.run_function(env, "get_rating_reviews_for_hotels",
                                     {"hotel_names": ["Le Marais Boutique"]})
print("rating:", repr(result)[:200], "| error:", error)

# 执行预订
result, error = runtime.run_function(env, "reserve_hotel",
                                     {"hotel": "Le Marais Boutique",
                                      "start_day": "2025-01-11",
                                      "end_day": "2025-01-15"})
print("reserve:", repr(result)[:120], "| error:", error)

output = [text_content_block_from_string("已预订 Le Marais Boutique，2025-01-11 至 2025-01-15。")]
print("utility(空环境+预订):", task.utility(env, output))
