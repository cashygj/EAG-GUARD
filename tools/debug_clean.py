#!/usr/bin/env python
"""干净任务下两臂的对话对照：看模型到底有没有发工具调用。

    python tools/debug_clean.py --user-task 1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eag_guard.bench.agentdojo_runner import make_pipeline  # noqa: E402
from eag_guard.llm import client_from_env  # noqa: E402


def dump(messages) -> None:
    for i, m in enumerate(messages):
        role = m.get("role")
        text = " ".join(b.get("content") or "" for b in (m.get("content") or []))[:200]
        calls = [f"{c.function}({dict(c.args)})" for c in (m.get("tool_calls") or [])]
        print(f"  [{i}] {role}: {text!r}")
        for c in calls:
            print(f"        -> {c[:150]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default="workspace")
    ap.add_argument("--user-task", default="1")
    ap.add_argument("--calls", type=int, default=3)
    args = ap.parse_args()

    from agentdojo.functions_runtime import FunctionsRuntime
    from agentdojo.task_suite.load_suites import get_suite

    client = client_from_env(ROOT / ".env")
    suite = get_suite("v1", args.suite)
    task = suite.get_user_task_by_id(f"user_task_{args.user_task}")

    for arm in ("undefended", "eag"):
        pipeline = make_pipeline(suite, client, arm, calls=args.calls)
        env = suite.load_and_inject_default_environment({})
        task_env = task.init_environment(env)
        runtime = FunctionsRuntime(suite.tools)
        _, _, task_env, messages, _ = pipeline.query(task.PROMPT, runtime, task_env)
        print(f"\n===== {arm} · user_task_{args.user_task} =====")
        dump(messages)
        utility = suite._check_task_result(task, messages[-1].get("content") or [],
                                           env, task_env, [])
        print(f"  utility = {utility}")
        if getattr(pipeline.executor, "records", None) is not None:
            print(f"  guard steps = {len(pipeline.executor.records)}")
            for r in pipeline.executor.records:
                print(f"    {'放行' if all(d.allowed for d in r.decisions) else '拦截'} "
                      f"{r.action.signature()[:110]}")
                for d in r.decisions:
                    if not d.allowed:
                        print(f"       {'；'.join(d.reasons)[:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
