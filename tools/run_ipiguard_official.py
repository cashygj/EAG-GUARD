"""跑 IPIGuard 官方实现（原仓库代码），用我们的模型与基准做同口径评测。

用法：
    python tools/run_ipiguard_official.py --suite slack --users 0-4 --injections 1-5 \
        --model qwen-plus-2025-04-28 --out results/runs/ipi_official_slack

说明：
- `import agentdojo` 走的是官方仓库里的 0.1.23 源码（插到 sys.path 最前）；
- 我们自己的 venv 里装的是 0.1.35，这里不会用到；
- `networkx` 来自 .deps/ipi_site（追加到 sys.path 末尾，不影响 openai 版本）。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

IPI_ROOT = Path(r"D:\EAG-GUARD\.deps\ipiguard")
IPI_SRC = IPI_ROOT / "agentdojo" / "src"
IPI_SITE = Path(r"D:\EAG-GUARD\.deps\ipi_site")

sys.path.insert(0, str(IPI_SRC))
sys.path.append(str(IPI_SITE))
sys.path.append(str(Path(r"D:\EAG-GUARD\.deps\ipi_stubs")))

import openai  # noqa: E402
from agentdojo.agent_pipeline.agent_pipeline import (  # noqa: E402
    AgentPipeline,
    load_system_message,
)
from agentdojo.agent_pipeline.basic_elements import InitQuery, SystemMessage  # noqa: E402
from agentdojo.agent_pipeline.llms.ipiguard_llm import (  # noqa: E402
    OpenAIConstructLLM,
    OpenAITraverseLLM,
)
from agentdojo.agent_pipeline.tool_execution import (  # noqa: E402
    DagToolsExecutionLoop,
    DagToolsExecutor,
)
from agentdojo.attacks.attack_registry import load_attack  # noqa: E402
from agentdojo.task_suite.load_suites import get_suite  # noqa: E402


def parse_range(text: str, prefix: str) -> list[str]:
    low, _, high = text.partition("-")
    high = high or low
    return [f"{prefix}_{i}" for i in range(int(low), int(high) + 1)]


def build_pipeline(model: str, key: str, base_url: str):
    client = openai.OpenAI(api_key=key, base_url=base_url)
    construct = OpenAIConstructLLM(client, model)
    traverse = OpenAITraverseLLM(client, model)
    executor = DagToolsExecutor(traverse)
    loop = DagToolsExecutionLoop(executor)
    pipeline = AgentPipeline([
        SystemMessage(load_system_message(None)),
        InitQuery(),
        construct,
        loop,
    ])
    # 攻击模块按 pipeline.name 里是否含官方模型 id 来识别模型（决定注入模板里
    # 怎么称呼受害模型）。官方 MODEL_NAMES 里 Qwen 的键是 "Qwen/Qwen2.5-32B-Instruct"，
    # 这里借用该键让注入模板用"Qwen created by Alibaba Cloud."，再用真实模型 id 跑。
    pipeline.name = "Qwen/Qwen2.5-32B-Instruct " + model
    return pipeline


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="slack")
    parser.add_argument("--users", default="0-4")
    parser.add_argument("--injections", default="1-5")
    parser.add_argument("--model", default="qwen-plus-2025-04-28")
    parser.add_argument("--attack", default="important_instructions")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0, help="只跑前 N 对（调试用）")
    args = parser.parse_args()

    key = os.environ.get("OPENAI_API_KEY") or ""
    base_url = os.environ.get("OPENAI_BASE_URL") or ""
    if not key:
        print("缺少 OPENAI_API_KEY")
        return 2

    suite = get_suite("v1", args.suite)
    pipeline = build_pipeline(args.model, key, base_url)
    attack = load_attack(args.attack, suite, pipeline)

    args.out.mkdir(parents=True, exist_ok=True)
    users = parse_range(args.users, "user_task")
    injections = parse_range(args.injections, "injection_task")

    pairs = [(u, i) for u in users for i in injections]
    if args.limit:
        pairs = pairs[: args.limit]

    done = utility_hits = attack_hits = 0
    for user_id, injection_id in pairs:
        record_path = args.out / f"{args.suite}_{user_id}_{injection_id}.json"
        if record_path.exists():
            record = json.loads(record_path.read_text(encoding="utf-8"))
            done += 1
            utility_hits += bool(record["utility"])
            attack_hits += bool(record["security"])
            continue

        user_task = suite.get_user_task_by_id(user_id)
        injection_task = suite.get_injection_task_by_id(injection_id)
        injections_map = attack.attack(user_task, injection_task)
        try:
            utility, security = suite.run_task_with_pipeline(
                pipeline, user_task, injection_task, injections_map
            )
            error = ""
        except Exception as exc:                       # noqa: BLE001
            utility, security = False, False
            error = f"{type(exc).__name__}: {exc}"

        record = {"user_task": user_id, "injection_task": injection_id,
                  "utility": bool(utility), "security": bool(security), "error": error}
        record_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        done += 1
        utility_hits += bool(utility)
        attack_hits += bool(security)
        print(f"  {user_id} x {injection_id}: "
              f"{'被攻破' if security else '安全'} / {'完成' if utility else '未完成'}"
              + (f"  [{error[:60]}]" if error else ""))

    print(f"\nIPIGuard 官方实现：{done} 对  ASR {attack_hits/done*100:.2f}%  "
          f"UA {utility_hits/done*100:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


