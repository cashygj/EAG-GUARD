"""对照组：完全用 AgentDojo 官方组件跑，不掺任何本仓库的脚手架。

目的：把"我们的适配层"与"模型/基准本身"分开。如果官方流水线在同一批
25 对上能到 0.7+，说明差距在我们自己的 executor / pipeline 包装里。

    python tools/official_baseline.py banking 0-4 1-5
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "D:/EAG-GUARD/src")

from agentdojo.agent_pipeline.agent_pipeline import (
    AgentPipeline,
    load_system_message,
    ToolsExecutionLoop,
)
from agentdojo.agent_pipeline.basic_elements import InitQuery, SystemMessage
from agentdojo.agent_pipeline.tool_execution import ToolsExecutor
from agentdojo.task_suite.load_suites import get_suite
from eag_guard.bench.agentdojo_runner import build_attack

from eag_guard.bench.agentdojo_runner import make_llm
from eag_guard.llm import client_from_env


def main() -> int:
    suite_name = sys.argv[1] if len(sys.argv) > 1 else "banking"
    user_range = sys.argv[2] if len(sys.argv) > 2 else "0-4"
    inj_range = sys.argv[3] if len(sys.argv) > 3 else "1-5"

    suite = get_suite("v1", suite_name)
    client = client_from_env("D:/EAG-GUARD/.env")
    llm = make_llm(client, "qwen-plus-2025-04-28")

    pipeline = AgentPipeline([
        SystemMessage(load_system_message(None)),
        InitQuery(),
        llm,
        ToolsExecutionLoop([ToolsExecutor(), llm], max_iters=15),
    ])

    def parse_range(text: str, prefix: str, total: int) -> list[str]:
        if text == "all":
            return [f"{prefix}_{i}" for i in range(total)]
        lo, _, hi = text.partition("-")
        hi = hi or lo
        return [f"{prefix}_{i}" for i in range(int(lo), int(hi) + 1)]

    user_ids = parse_range(user_range, "user_task", len(suite.user_tasks))
    inj_ids = parse_range(inj_range, "injection_task", len(suite.injection_tasks))

    attack = build_attack("important_instructions", suite, pipeline, model_label="qwen-plus")

    done = 0
    total = 0
    attacks = 0
    completed = 0
    for user_id in user_ids:
        for inj_id in inj_ids:
            user_task = suite.get_user_task_by_id(user_id)
            inj_task = suite.get_injection_task_by_id(inj_id)
            # 用攻击对象自己生成注入内容，再据此构造环境（官方跑法）
            injections = attack.attack(user_task, inj_task)
            environment = suite.load_and_inject_default_environment(injections)
            total += 1
            try:
                utility, security = suite.run_task_with_pipeline(
                    agent_pipeline=pipeline, user_task=user_task,
                    injection_task=inj_task, injections=injections,
                    environment=environment,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"  {user_id} x {inj_id}: 异常 {type(exc).__name__}: {exc}"[:160])
                continue
            done += 1
            attacks += int(security)
            completed += int(utility)
            mark = "完成" if utility else "未完成"
            print(f"  {user_id} x {inj_id}: {mark} / {'被攻破' if security else '安全'}")

    print(f"\n官方流水线：{done} 对  ASR {attacks / max(done, 1):.2%}  UA {completed / max(done, 1):.2%}")
    print("（效用见上面每行的『完成/未完成』计数）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
