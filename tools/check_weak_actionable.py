"""验证弱反馈分支也会带上「正确的取值」。"""

import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from eag_guard.integrations.agentdojo import EAGGuardElement
from eag_guard.judge import RuleJudge
from eag_guard.pipeline import Action, Decision, Guard, GuardConfig, StepRecord
from eag_guard.types import EvidenceItem, Provenance, Trust

import dataclasses


class StubParser:
    def parse(self, request, tools=None):
        from eag_guard.scope import AuthorizationScope
        return AuthorizationScope(tools=frozenset({"send_money"}), objects={},
                                  params={}, request_text=request)


guard = Guard(parser=StubParser(), planner_factory=lambda *a: None, judge=RuleJudge(),
              tools={}, config=GuardConfig(delegation="untargeted"))
element = EAGGuardElement(guard, executor=None, domain="banking", feedback="weak")
element.evidence.append(EvidenceItem(
    id="read_file:1#bill", source="file", trust=Trust.UNTRUSTED,
    text="Total 98.70", fields={"recipient": "UK12345678901234567890", "amount": "98.70"},
    authorized=True, producer="read_file"))

from eag_guard.types import Attribution
item = type("I", (), {"param": "recipient",
                      "attribution": Attribution(param="recipient", value="US133",
                                                 provenance=Provenance.INJECTED)})()
record = StepRecord(index=0, action=Action("a1", "send_money", {"recipient": "US133"}),
                    attributions=(item,),
                    decisions=[Decision("fpr", False, ("越权",))])
call = type("C", (), {"function": "send_money"})()
notice = element._recovery_notice([(call, record)])
print(notice)
print("\n包含正确的取值：", "正确的取值" in notice, "| 含账单 IBAN：", "UK12345678901234567890" in notice)
