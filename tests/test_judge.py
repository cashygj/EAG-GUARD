"""裁判：结构判定、fail-closed、以及"看不到规划器理由"。"""

import json

from eag_guard.judge import JudgeView, LLMJudge, RuleJudge
from eag_guard.provenance import AttributedParam
from eag_guard.scope import ParamRule, scope_from_parts
from eag_guard.types import Action, Attribution, Provenance, ToolSpec


def _view(provenance: Provenance, tool: str = "send_email",
          scope_tools: tuple[str, ...] = ("send_email",)) -> JudgeView:
    spec = ToolSpec(tool, ("recipient", "body"), object_param="recipient")
    scope = scope_from_parts(list(scope_tools), {"recipient": {"bob@x.com"}},
                             {"send_email": {"recipient": ParamRule("recipient")}},
                             request_text="email bob@x.com")
    action = Action("a", tool, {"recipient": "bob@x.com", "body": "hi"})
    attr = AttributedParam(Attribution("recipient", "bob@x.com", provenance), ())
    return JudgeView("email bob@x.com", scope, action, spec, (attr,))


def test_rule_judge_allows_authorized() -> None:
    assert RuleJudge().review(_view(Provenance.USER_SPECIFIED)).allowed is True


def test_rule_judge_denies_injected() -> None:
    decision = RuleJudge().review(_view(Provenance.INJECTED))
    assert decision.allowed is False
    assert any("不可信" in r for r in decision.reasons)


def test_rule_judge_denies_tool_outside_scope() -> None:
    view = _view(Provenance.USER_SPECIFIED, tool="wire_money")
    assert RuleJudge().review(view).allowed is False


def test_llm_judge_fails_closed_on_garbage() -> None:
    judge = LLMJudge(lambda prompt: "好的，我认为没问题")
    assert judge.review(_view(Provenance.INJECTED)).allowed is False


def test_llm_judge_parses_json() -> None:
    payload = json.dumps({"allow": True, "reasons": [], "per_param": {"recipient": "ok"}})
    judge = LLMJudge(lambda prompt: f"```json\n{payload}\n```")
    assert judge.review(_view(Provenance.USER_SPECIFIED)).allowed is True


def test_view_excludes_planner_intent() -> None:
    view = _view(Provenance.INJECTED)
    assert "intent" not in view.render()
