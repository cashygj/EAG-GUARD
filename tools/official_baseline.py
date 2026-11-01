"""对照组：完全用 AgentDojo 官方组件跑，不掺任何本仓库的脚手架。

目的：把"我们的适配层"与"模型/基准本身"分开。如果官方流水线在同一批
25 对上能到 0.7+，说明差距在我们自己的 executor / pipeline 包装里。

    python tools/official_baseline.py banking 0-4 1-5
"""

from __future__ import annotations

import sys
import argparse
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agentdojo.agent_pipeline.tool_execution import ToolsExecutor
from agentdojo.task_suite.load_suites import get_suite
from eag_guard.bench.agentdojo_runner import (
    build_attack, build_pipeline, RecordingExecutor, TaskPipeline, run_pairs, summarize_runs,
)

from eag_guard.bench.agentdojo_runner import make_llm
from eag_guard.llm import client_from_env


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", nargs="?", default="banking")
    parser.add_argument("users", nargs="?", default="0-4")
    parser.add_argument("injections", nargs="?", default="1-5")
    parser.add_argument("--model", default="qwen-plus-2025-04-28")
    parser.add_argument("--attack-model-label", default=None)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    suite_name, user_range, inj_range = args.suite, args.users, args.injections

    suite = get_suite("v1", suite_name)
    client = client_from_env(ROOT / ".env")
    llm = make_llm(client, args.model)

    executor = RecordingExecutor(ToolsExecutor())
    pipeline = TaskPipeline(build_pipeline(llm, executor), executor,
                            name=f"{args.model}-official", model=args.model, llm=llm)

    def parse_range(text: str, prefix: str, available: dict) -> list[str]:
        if text == "all":
            return list(available)
        lo, _, hi = text.partition("-")
        hi = hi or lo
        return [f"{prefix}_{i}" for i in range(int(lo), int(hi) + 1)]

    user_ids = parse_range(user_range, "user_task", suite.user_tasks)
    inj_ids = parse_range(inj_range, "injection_task", suite.injection_tasks)
    if any(key not in suite.user_tasks for key in user_ids) or any(
            key not in suite.injection_tasks for key in inj_ids):
        parser.error("unknown task id; use all to select the suite's actual task IDs")

    attack = build_attack("important_instructions", suite, pipeline,
                          model_label=args.attack_model_label)

    out = args.out or ROOT / "results" / "runs" / f"official_{suite_name}_{time.strftime('%Y%m%d-%H%M%S')}"
    if out.exists():
        parser.error(f"output directory exists; use a new --out: {out}")
    out.mkdir(parents=True)
    pairs = [(u, i) for u in user_ids for i in inj_ids]

    def report(run):
        print(f"{run.user_task_id} x {run.injection_task_id}: "
              f"utility={run.utility} security={run.security} error={run.error}")

    runs = run_pairs(suite, pairs, pipeline, attack, out_dir=out, on_result=report)
    metadata = {"model": args.model, "suite": suite_name, "arm": "undefended",
                "scaffold": "official", "temperature": 0.0, "pairs": len(pairs),
                "attack_model_label": args.attack_model_label or args.model,
                "table": summarize_runs(runs, suite).as_table(),
                "errors": [r.to_dict() for r in runs if r.error]}
    (out / "summary.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata["table"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
