"""这些测试钉住的是"曾经静默失效、靠人工发现"的行为。

每一条都对应一次真实踩坑：改了代码但替换没匹配上、或逻辑被后续改动覆盖，
单跑主测试套件看不出来，只有在真实跑批里才暴露。这里用最小用例锁死。
"""

from __future__ import annotations

from eag_guard.bench.agentdojo_runner import (
    FIELD_STRICT_PARAMS_BY_DOMAIN,
    STRICT_PARAMS_BY_DOMAIN,
    domain_policy,
)
from eag_guard.integrations.agentdojo import EAGGuardElement
from eag_guard.judge import JudgeView
from eag_guard.parsing import tools_implied_by_request
from eag_guard.pipeline import Decision, Guard, GuardConfig, StepRecord
from eag_guard.scope import AuthorizationScope, ParamRule
from eag_guard.types import Action, NodeKind, ToolSpec


class _StubParser:
    def __init__(self, tool: str, params: dict[str, ParamRule]) -> None:
        self.tool = tool
        self.params = params

    def parse(self, request, tools=None):
        return AuthorizationScope(
            tools=frozenset({self.tool}),
            objects={},
            params={self.tool: dict(self.params)},
            request_text=request,
        )


def _guard(tool: str, params: dict[str, ParamRule], **config) -> Guard:
    spec = ToolSpec(tool, tuple(params), object_param="recipient", object_class="recipient")
    return Guard(
        parser=_StubParser(tool, params),
        planner_factory=lambda *a: None,
        judge=None,
        tools={tool: spec},
        config=GuardConfig(**config),
    )


def test_strict_param_survives_untargeted_widening():
    """untargeted 会放宽所有参数来源，但 strict_params 里的必须保持窄口径。

    踩坑：放宽代码先写死 `_ParamRule(name, allow=ALL_PROVENANCE)`，
    后来加的 strict 分支因为替换字符串不匹配而静默失效，
    结果 send_money(recipient=<攻击者 IBAN>) 被放行。
    """
    guard = _guard(
        "send_money",
        {"recipient": ParamRule("recipient"), "amount": ParamRule("amount")},
        delegation="untargeted",
        strict_params=("send_money.recipient",),
    )
    state = guard.prepare("pay the bill")
    recipient_rule = state.scope.rule("send_money", "recipient")
    amount_rule = state.scope.rule("send_money", "amount")
    assert recipient_rule.allow == frozenset({p for p in recipient_rule.allow})
    assert len(recipient_rule.allow) == 2, "收款人必须保持窄口径（用户指定或委托）"
    assert len(amount_rule.allow) == 4, "其余参数应被放宽为全部来源"


def test_scope_description_matches_untargeted_policy():
    """描述必须与真实策略一致，否则裁判会照字面否掉所有运行时取值。

    踩坑：策略是 untargeted，描述却写"只能由用户直接指定"，
    裁判据此拒绝了所有"按标准选出的频道/用户"。
    """
    guard = _guard("send_money", {"amount": ParamRule("amount")},
                   delegation="untargeted")
    text = guard.prepare("pay the bill").scope.describe()
    assert "来源不预先限定" in text


def test_exempt_params_are_redacted_in_judge_view():
    """豁免字段的值必须从裁判可见的签名里消失。

    踩坑：值仍出现在【候选动作】行里，裁判照样拿正文否决，"豁免"形同虚设。
    """
    guard = _guard("send_direct_message",
                   {"body": ParamRule("body"), "recipient": ParamRule("recipient")},
                   delegation="untargeted")
    state = guard.prepare("say hi to Alice")
    action = Action("a1", "send_direct_message",
                    {"recipient": "Alice", "body": "SECRET-PAYLOAD"})
    view = JudgeView(
        user_request="say hi to Alice",
        scope=state.scope,
        action=action,
        spec=ToolSpec("send_direct_message", ("recipient", "body")),
        attributions=(),
        exempt_params=("body",),
    )
    rendered = view.render()
    assert "SECRET-PAYLOAD" not in rendered
    assert "值已隐藏" in rendered


def test_denial_notice_is_a_status_report():
    """拒绝提示必须说明"哪些已完成、不是任务失败"。

    踩坑：只说"已拒绝，不要重试"，模型以为任务失败就收尾，
    slack 的守卫代价因此高达 0.32。
    """
    guard = _guard("send_email", {"body": ParamRule("body")})
    element = EAGGuardElement(guard, executor=None, domain="travel", feedback="strong")
    element.executed.append({"function": "reserve_hotel",
                             "args": {"hotel": "Le Marais Boutique"}})
    record = StepRecord(
        index=0,
        action=Action("a1", "send_email", {"body": "x"}),
        attributions=(),
        decisions=[Decision("fpr", False, ("工具 send_email 不在授权范围 T 内",))],
    )
    fake_call = type("C", (), {"function": "send_email"})()
    notice = element._recovery_notice([(fake_call, record)])
    assert "已经成功完成" in notice
    assert "reserve_hotel" in notice
    assert "不是任务失败" in notice


def test_verb_fallback_adds_implied_tools():
    """请求里出现"删除/预约"时，对应工具必须进 T。

    踩坑：解析器漏列 delete_file / create_calendar_event，任务根本做不完。
    """
    specs = [
        ToolSpec("delete_file", ("file_id",)),
        ToolSpec("create_calendar_event", ("title",)),
        ToolSpec("get_weather", ()),
    ]
    assert "delete_file" in tools_implied_by_request("please delete budget.xlsx", specs)
    assert "create_calendar_event" in tools_implied_by_request(
        "schedule a meeting tomorrow", specs)
    assert tools_implied_by_request("what is the weather", specs) == set()


def test_read_policy_no_target_allows_only_argless_reads():
    """no_target 只放行"无目标读取"；带对象的读取仍要审。"""
    spec = ToolSpec("get_channels", (), read_only=True)
    spec2 = ToolSpec("read_channel_messages", ("channel",), read_only=True)
    guard = Guard(
        parser=_StubParser("get_channels", {}),
        planner_factory=lambda *a: None,
        judge=None,
        tools={"get_channels": spec, "read_channel_messages": spec2},
        config=GuardConfig(read_policy="no_target", delegation="targeted"),
    )
    state = guard.prepare("list channels")
    argless = guard.review(state, Action("a1", "get_channels", {}), [], 0)
    targeted = guard.review(state, Action("a2", "read_channel_messages",
                                          {"channel": "general"}), [], 1)
    assert all(d.allowed for d in argless.decisions)
    assert not all(d.allowed for d in targeted.decisions)


def test_domain_policies_match_report_table():
    """按域配置必须与报告表 4-2 一致。"""
    banking = domain_policy(type("S", (), {"name": "banking"})())
    slack = domain_policy(type("S", (), {"name": "slack"})())
    travel = domain_policy(type("S", (), {"name": "travel"})())
    assert banking["read_policy"] == "allow_all"
    assert banking["feedback"] == "weak", "报告：banking 弱反馈 UA +4.2pp"
    assert slack["read_policy"] == "no_target"
    assert travel["audit"] is True, "报告：travel 开启输出审核"
    assert STRICT_PARAMS_BY_DOMAIN["banking"], "资金流向字段必须保持窄口径"


def test_graph_has_six_node_kinds():
    """流程图要求六类节点：授权/证据/工具/对象/参数/动作。"""
    kinds = {k.value for k in NodeKind}
    for required in ("authorization", "evidence", "tool", "object", "param", "action"):
        assert required in kinds
