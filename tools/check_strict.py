import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from eag_guard.judge import RuleJudge
from eag_guard.pipeline import Guard, GuardConfig
from eag_guard.scope import AuthorizationScope, ParamRule
from eag_guard.types import ToolSpec


class StubParser:
    def parse(self, request, tools=None):
        return AuthorizationScope(
            tools=frozenset({"send_money"}),
            objects={},
            params={"send_money": {
                "recipient": ParamRule("recipient"),
                "amount": ParamRule("amount"),
            }},
            request_text=request,
        )


spec = ToolSpec("send_money", ("recipient", "amount"), object_param="recipient",
                object_class="recipient")
guard = Guard(parser=StubParser(), planner_factory=lambda *a: None,
              judge=RuleJudge(), tools={spec.name: spec},
              config=GuardConfig(delegation="untargeted",
                                 strict_params=("send_money.recipient",)))
state = guard.prepare("pay the bill")
print(state.scope.describe())
