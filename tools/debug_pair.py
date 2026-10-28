#!/usr/bin/env python
"""调试单对：把对话、环境差异、官方判定都摊开看。

    python tools/debug_pair.py --suite workspace --user-task 0 --injection-task 0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eag_guard.bench.agentdojo_runner import build_attack, make_pipeline  # noqa: E402
from eag_guard.llm import client_from_env  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="workspace")
    parser.add_argument("--user-task", default="0")
    parser.add_argument("--injection-task", default="0")
    parser.add_argument("--arm", default="eag")
    args = parser.parse_args()

    from agentdojo.functions_runtime import FunctionsRuntime
    from agentdojo.task_suite.load_suites import get_suite
    from agentdojo.types import get_text_content_as_str  # noqa: F401

    client = client_from_env(ROOT / ".env")
    suite = get_suite("v1", args.suite)
    pipeline = make_pipeline(suite, client, args.arm)
    attack = build_attack("important_instructions", suite, pipeline)

    user_task = suite.get_user_task_by_id(f"user_task_{args.user_task}")
    injection_task = suite.get_injection_task_by_id(f"injection_task_{args.injection_task}")
    injections = attack.attack(user_task, injection_task)

    env = suite.load_and_inject_default_environment(injections)
    task_env = user_task.init_environment(env)
    pre = task_env.model_copy(deep=True)

    runtime = FunctionsRuntime(suite.tools)
    _, _, task_env, messages, _ = pipeline.query(user_task.PROMPT, runtime, task_env)

    print("=== 注入点 ===")
    for key in list(injections)[:5]:
        print(f"  {key}")
    print(f"\n=== 消息 {len(messages)} 条 ===")
    for i, m in enumerate(messages):
        role = m.get("role")
        text = ""
        if m.get("content"):
            text = " ".join(b.get("content") or "" for b in m["content"])[:300]
        calls = [f"{c.function}({dict(c.args)})" for c in (m.get("tool_calls") or [])]
        print(f"[{i}] {role}: {text!r}")
        for c in calls:
            print(f"      -> {c}")

    from agentdojo.types import text_content_block_from_string  # noqa: F401

    output = None
    for m in reversed(messages):
        if m.get("role") == "assistant" and m.get("content"):
            output = " ".join(b.get("content") or "" for b in m["content"])
            break
    print("\n=== 最终输出 ===")
    print(output)

    stack = []
    print("\n=== 官方判定 ===")
    import inspect

    check = suite._check_task_result
    print("  signature:", inspect.signature(check))
    from agentdojo.task_suite.task_suite import functions_stack_trace_from_messages

    trace = functions_stack_trace_from_messages(messages)
    utility = suite._check_task_result(user_task, [], pre, task_env, trace)
    security = suite._check_task_result(injection_task, [], pre, task_env, trace)
    print("  utility :", utility)
    print("  security:", security)
    print("  injection GOAL:", injection_task.GOAL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
