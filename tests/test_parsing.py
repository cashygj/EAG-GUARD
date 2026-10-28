"""任务解析：白名单校验、fail-closed、JSON 提取。"""

import pytest

from eag_guard.parsing import LLMScopeParser, extract_json
from eag_guard.scope import RuleScopeParser, DomainPack
from eag_guard.types import ToolSpec

TOOLS = [
    ToolSpec("get_balance", (), read_only=True, side_effect=False),
    ToolSpec("read_file", ("file_path",), object_param="file_path", object_class="file",
             read_only=True, side_effect=False),
    ToolSpec("send_money", ("recipient", "amount", "subject"),
             object_param="recipient", object_class="recipient"),
    ToolSpec("send_email", ("recipients", "body"),
             object_param="recipients", object_class="recipient"),
]

GOOD = """
{"tools": ["read_file", "send_money"],
 "objects": {"file": ["bill.txt"]},
 "delegations": [{"tool": "send_money", "param": "amount", "source": "file", "mode": "field"}],
 "notes": "读账单后付款"}
"""


def _parser(reply):
    return LLMScopeParser(lambda messages: reply)


def test_parses_valid_scope() -> None:
    parser = _parser(GOOD)
    scope = parser.parse("pay the bill in bill.txt", TOOLS)
    assert {"read_file", "send_money"} <= scope.tools
    assert "get_balance" in scope.tools          # 只读工具默认放行
    assert scope.objects["file"] == frozenset({"bill.txt"})
    rule = scope.rule("send_money", "amount")
    assert rule.delegable is True
    assert rule.delegation_source == "file"
    assert rule.mode == "field"
    assert parser.last.error is None


def test_drops_unknown_tool() -> None:
    parser = _parser('{"tools": ["send_money", "wire_money"], "objects": {}, "delegations": []}')
    scope = parser.parse("pay", TOOLS)
    assert "send_money" in scope.tools
    assert "wire_money" not in scope.tools
    assert any("wire_money" in d for d in parser.last.dropped)


def test_read_only_tools_always_authorized() -> None:
    """读操作不受 T 约束：模型换个检索路径不该被当成越权。"""
    parser = _parser('{"tools": ["send_money"], "objects": {}, "delegations": []}')
    scope = parser.parse("pay", TOOLS)
    assert {"send_money", "get_balance", "read_file"} <= scope.tools


def test_drops_unknown_object_class() -> None:
    parser = _parser('{"tools": ["send_money"], "objects": {"planet": ["mars"]}, "delegations": []}')
    scope = parser.parse("pay", TOOLS)
    assert "planet" not in scope.objects
    assert any("planet" in d for d in parser.last.dropped)


def test_rejects_content_delegation_on_sensitive_param() -> None:
    reply = ('{"tools": ["send_money"], "objects": {}, "delegations": '
             '[{"tool": "send_money", "param": "amount", "source": "inbox", "mode": "content"}]}')
    parser = _parser(reply)
    scope = parser.parse("pay what the email says", TOOLS)
    assert scope.rule("send_money", "amount").delegable is False
    assert any("敏感字段" in d for d in parser.last.dropped)


def test_rejects_delegation_on_unauthorized_tool() -> None:
    reply = ('{"tools": ["read_file"], "objects": {}, "delegations": '
             '[{"tool": "send_money", "param": "amount", "source": "x"}]}')
    parser = _parser(reply)
    scope = parser.parse("read the file", TOOLS)
    assert "send_money" not in scope.tools
    assert scope.rule("send_money", "amount").delegable is False


def test_falls_back_to_read_only_on_garbage() -> None:
    parser = _parser("抱歉，我无法解析这个请求。")
    scope = parser.parse("pay the bill", TOOLS)
    assert parser.last.fallback is True
    assert scope.tools == {"get_balance", "read_file"}
    assert "send_money" not in scope.tools
    assert any("解析失败" in note for note in scope.notes)


def test_retries_once_then_parses() -> None:
    replies = iter(["not json at all", GOOD])
    parser = LLMScopeParser(lambda messages: next(replies))
    scope = parser.parse("pay the bill", TOOLS)
    assert "send_money" in scope.tools
    assert parser.last.fallback is False


def test_extract_json_handles_fences() -> None:
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('前缀 {"a": 2} 后缀') == {"a": 2}
    assert extract_json("没有 json") is None


CAL_TOOLS = [
    ToolSpec("get_day_calendar_events", ("day",), object_param="day",
             object_class="day", read_only=True, side_effect=False),
    ToolSpec("create_calendar_event",
             ("title", "start_time", "end_time", "participants", "location"),
             object_param="participants", object_class="participant"),
    ToolSpec("delete_file", ("file_id",), object_param="file_id", object_class="file"),
]


def test_temporal_params_are_not_checked() -> None:
    parser = _parser('{"tools": ["create_calendar_event"], "objects": {}, "delegations": []}')
    scope = parser.parse("schedule a lunch tomorrow at noon", CAL_TOOLS)
    from eag_guard.types import Provenance

    rule = scope.rule("create_calendar_event", "start_time")
    assert rule.permits(Provenance.UNATTRIBUTED)
    assert rule.permits(Provenance.INJECTED)
    # 参与者（可以去外泄）仍然是严格字段
    assert not scope.rule("create_calendar_event", "participants").permits(Provenance.INJECTED)


def test_object_ids_delegate_only_to_their_own_domain() -> None:
    parser = _parser('{"tools": ["delete_file"], "objects": {}, "delegations": []}')
    scope = parser.parse("delete the file I mentioned", CAL_TOOLS)
    rule = scope.rule("delete_file", "file_id")
    assert rule.allows_delegation is True
    assert rule.delegation_source == "file"
