"""把 mock 用例跑成与报告同形的结果表。"""

from __future__ import annotations

from typing import Mapping, Sequence

from ..audit import NullAudit, OutputAudit
from ..eval.metrics import CaseOutcome, Summary, summarize
from ..judge import Judge, RuleJudge
from ..pipeline import Guard, GuardConfig, Trace
from ..scope import RuleScopeParser
from .mock import (
    PACK,
    TOOLS,
    MockCase,
    MockEnvironment,
    ScriptedPlanner,
    default_cases,
    evaluate,
)

UNDEFENDED = GuardConfig(name="undefended", enable_fpr=False, enable_judge=False,
                         output_audit=False)
# 离线 mock 测的是"结构判定"这条路径，用 targeted；真实基准用 untargeted（报告主配置）。
EAG = GuardConfig(name="eag", delegation="targeted")

#: 报告 §4.3 的对照臂，按需增补。
ARMS: dict[str, GuardConfig] = {
    "undefended": UNDEFENDED,
    "eag": EAG,
}


def run_case(case: MockCase, config: GuardConfig | None = None,
             judge: Judge | None = None) -> tuple[CaseOutcome, Trace]:
    config = config or GuardConfig()
    case.world.reset()
    env = MockEnvironment(case.world)
    guard = Guard(
        parser=RuleScopeParser(PACK),
        planner_factory=lambda request, scope: ScriptedPlanner(case, scope),
        judge=judge or RuleJudge(),
        tools=TOOLS,
        config=config,
        audit=OutputAudit() if config.output_audit else NullAudit(),
    )
    trace = guard.run(case.request, env, case.id)
    return evaluate(case, trace, case.world), trace


def run_all(cases: Sequence[MockCase] | None = None,
            configs: Mapping[str, GuardConfig] | None = None
            ) -> dict[str, tuple[Summary, list[Trace]]]:
    cases = list(cases or default_cases())
    configs = dict(configs or ARMS)
    results: dict[str, tuple[Summary, list[Trace]]] = {}
    for name, config in configs.items():
        outcomes: list[CaseOutcome] = []
        traces: list[Trace] = []
        for case in cases:
            outcome, trace = run_case(case, config)
            outcomes.append(outcome)
            traces.append(trace)
        results[name] = (summarize(outcomes), traces)
    return results
