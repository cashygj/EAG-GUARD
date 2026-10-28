"""指标口径必须与报告表 4-1 自洽。

这组断言是把报告冻结成基线后的第一道校验：以后任何重跑，只要口径跑偏，
这里就会先红。
"""

import pytest

from eag_guard.eval.metrics import (
    CaseOutcome,
    aggregate_from_domain_stats,
    mcnemar,
    summarize,
)

# 报告表 4-1：域 -> (对数, 无防御 ASR, 无防御 UA)
UNDEFENDED = {
    "workspace": (240, 0.1708, 0.6333),
    "slack": (105, 0.9429, 0.7238),
    "travel": (140, 0.6214, 0.2643),
    "banking": (144, 0.6389, 0.7569),
}
# 报告表 4-1：域 -> (对数, EAG ASR, EAG UA)
DEFENDED = {
    "workspace": (240, 0.0000, 0.7708),
    "slack": (105, 0.0190, 0.6667),
    "travel": (140, 0.0143, 0.6429),
    "banking": (144, 0.0000, 0.7153),
}


def test_undefended_totals_match_report() -> None:
    agg = aggregate_from_domain_stats(UNDEFENDED)
    assert agg["n"] == 629
    assert agg["asr"] == pytest.approx(0.5072, abs=1e-3)
    assert agg["ua"] == pytest.approx(0.5946, abs=1e-4)
    assert agg["eq_asr"] == pytest.approx(0.5935, abs=1e-4)
    assert agg["eq_ua"] == pytest.approx(0.5946, abs=1e-4)


def test_defended_totals_match_report() -> None:
    agg = aggregate_from_domain_stats(DEFENDED)
    assert agg["asr"] == pytest.approx(0.0064, abs=1e-3)
    assert agg["ua"] == pytest.approx(0.7122, abs=1e-4)
    assert agg["eq_asr"] == pytest.approx(0.0083, abs=1e-4)
    assert agg["eq_ua"] == pytest.approx(0.6989, abs=1e-4)


def test_tool_level_asr_denominator() -> None:
    assert 292 / 609 == pytest.approx(0.4795, abs=1e-4)


def test_summary_roundtrip() -> None:
    outcomes = [
        CaseOutcome("banking", "u1", "i1", attack_success=True, attack_via_tool=True, utility=True),
        CaseOutcome("banking", "u1", "i2", attack_success=False, utility=True),
        CaseOutcome("slack", "u2", "i1", attack_success=True, attack_via_tool=False,
                    utility=False, tool_attack_applicable=False),
    ]
    summary = summarize(outcomes)
    assert summary.by_pair.n == 3
    assert summary.by_pair.asr == pytest.approx(2 / 3)
    assert summary.by_pair.ua == pytest.approx(2 / 3)
    assert summary.tool_asr == pytest.approx(1 / 2)
    assert summary.equal_weight_asr == pytest.approx((1.0 + 0.5) / 2)
    assert {r["域"] for r in summary.as_table()} == {"banking", "slack", "合计（按对）", "合计（等权）"}


def test_mcnemar_counts() -> None:
    pairs = [(True, False)] * 316 + [(False, True)] * 1
    counts = mcnemar(pairs)
    assert counts["fixed"] == 316
    assert counts["broken"] == 1


def test_agentdojo_security_sign() -> None:
    """AgentDojo v1 的 security() 返回"注入目标是否完成"，方向与名字相反。"""
    from eag_guard.eval.metrics import outcome_from_agentdojo

    safe = outcome_from_agentdojo("banking", "u", "i", utility=True, security=False)
    hit = outcome_from_agentdojo("banking", "u", "i", utility=True, security=True)
    assert safe.attack_success is False
    assert hit.attack_success is True
    assert safe.utility is True and hit.utility is True


def test_agentdojo_tool_surface_requires_trace() -> None:
    from eag_guard.eval.metrics import outcome_from_agentdojo

    unknown = outcome_from_agentdojo("banking", "u", "i", utility=True, security=True)
    assert unknown.tool_attack_applicable is False   # 没有 trace 就不计入工具级
    known = outcome_from_agentdojo("banking", "u", "i", utility=True, security=True,
                                   attack_via_tool=True)
    assert known.tool_attack_applicable is True
