import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from eag_guard.provenance import AttributionContext, Attributor
from eag_guard.scope import ParamRule, scope_from_parts
from eag_guard.types import Action, EvidenceItem, ToolSpec, Trust

spec = ToolSpec("send_email", ("recipients", "subject", "body"),
                object_param="recipients", object_class="recipient")
scope = scope_from_parts(["send_email"], {"recipient": {"bob@example.com"}},
                         request_text="email bob@example.com the report")
action = Action("a1", "send_email", {
    "recipients": ["bob@example.com"],      # 列表参数
    "subject": "report",
    "body": "hi",
})
ctx = AttributionContext(user_request="email bob@example.com the report", evidence=[])
result = Attributor().attribute(action, spec, scope, ctx)
for item in result:
    print(item.param, "=", repr(item.value), "->", item.provenance.value, "|", item.attribution.note)
