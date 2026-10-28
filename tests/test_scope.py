"""授权范围推导：T/O/P 必须只来自用户请求。"""

from eag_guard.bench.mock import PACK
from eag_guard.scope import RuleScopeParser


def test_extracts_recipient_whitelist() -> None:
    scope = RuleScopeParser(PACK).parse(
        "Read the Q3 summary from the inbox and email it to bob@example.com."
    )
    assert "send_email" in scope.tools
    assert scope.objects["recipient"] == frozenset({"bob@example.com"})
    assert scope.object_allowed("send_email", "attacker@evil.com",
                                PACK.tools["send_email"]) is False


def test_delegation_requires_cue() -> None:
    parser = RuleScopeParser(PACK)
    plain = parser.parse("Pay invoice INV-88.")
    assert plain.rule("pay_invoice", "payee").allows_delegation is False

    delegated = parser.parse("Pay invoice INV-88. The payee is listed there.")
    assert delegated.rule("pay_invoice", "payee").allows_delegation is True
    assert delegated.rule("pay_invoice", "payee").mode == "field"


def test_money_params_are_field_mode() -> None:
    scope = RuleScopeParser(PACK).parse(
        "Pay the invoice in the inbox, the amount is listed there."
    )
    assert scope.rule("pay_invoice", "amount").mode == "field"
    assert scope.rule("pay_invoice", "payee").mode == "field"


def test_content_params_are_content_mode() -> None:
    scope = RuleScopeParser(PACK).parse(
        "Send an email to bob@example.com with the body from the inbox."
    )
    assert scope.rule("send_email", "body").mode == "content"
    assert scope.rule("send_email", "recipient").allows_delegation is False


def test_unknown_tool_not_granted() -> None:
    scope = RuleScopeParser(PACK).parse("Tell me a joke.")
    assert "pay_invoice" not in scope.tools


def test_url_object_ignores_scheme_and_www() -> None:
    """对象白名单不能因为 http:// 前缀或 www. 就判用户自己给的 URL 越权。"""
    from eag_guard.types import ToolSpec

    scope = RuleScopeParser(PACK).parse("read www.dora-website.com")
    spec = ToolSpec("get_webpage", ("url",), object_param="url", object_class="url",
                    read_only=True, side_effect=False)
    scope = type(scope)(
        tools=scope.tools, objects={"url": frozenset({"www.dora-website.com"})},
        params=scope.params, request_text=scope.request_text,
    )
    assert scope.object_allowed("get_webpage", "http://www.dora-website.com", spec) is True
    assert scope.object_allowed("get_webpage", "https://WWW.Dora-Website.com/", spec) is True
    assert scope.object_allowed("get_webpage", "www.evil.com", spec) is False
