"""EAG-Guard：基于授权不变式的工具型智能体注入防御。

对外只需要一个 Guard：给它解析器、规划器、裁判和环境，它负责在动作执行前
判定是否越权。其余模块可以按需替换（例如把 RuleJudge 换成 LLMJudge）。
"""

from .audit import AuditResult, NullAudit, OutputAudit
from .eag import EAG, FPRResult
from .judge import JudgeView, LLMJudge, RuleJudge
from .pipeline import Execution, Guard, GuardConfig, Trace
from .provenance import AttributionContext, Attributor
from .scope import AuthorizationScope, DomainPack, ParamRule, RuleScopeParser
from .types import (
    Action,
    Attribution,
    Decision,
    EvidenceItem,
    Provenance,
    ToolResult,
    ToolSpec,
    Trust,
)

__all__ = [
    "Action", "Attribution", "AttributionContext", "Attributor", "AuditResult",
    "AuthorizationScope", "Decision", "DomainPack", "EAG", "EvidenceItem",
    "Execution", "FPRResult", "Guard", "GuardConfig", "JudgeView", "LLMJudge",
    "NullAudit", "OutputAudit", "ParamRule", "Provenance", "RuleJudge",
    "RuleScopeParser", "ToolResult", "ToolSpec", "Trace", "Trust",
]
