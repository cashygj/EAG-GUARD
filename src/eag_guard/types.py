"""Core data types for EAG-Guard.

对应报告 §2.2 的形式化定义：

    u            用户请求
    A = (T, O, P) 授权范围：允许的工具 / 允许作用的对象 / 参数来源约束
    s(v)         参数值来源：user-specified | user-delegated | injected

不变式：若存在 v 使 s(v)=injected，则动作不得执行（除非用户显式重新授权）。
动作 supported 当且仅当 tool∈T、object∈O、且每个参数值的 s(v) 属于前两类。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class Trust(str, Enum):
    """证据可信度。只有用户请求与系统提示是 TRUSTED。"""

    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"

    def __str__(self) -> str:  # pragma: no cover - 便于日志阅读
        return {"trusted": "可信", "untrusted": "不可信"}[self.value]


class Provenance(str, Enum):
    """参数值来源 s(v)——报告 §2.2 的三分类，外加一个保守兜底类。"""

    USER_SPECIFIED = "user_specified"   # 直接出现在用户请求（或可信内容）中
    USER_DELEGATED = "user_delegated"   # 用户指定该字段由某来源运行时取值
    INJECTED = "injected"               # 只出现在不可信内容中且未被委托
    UNATTRIBUTED = "unattributed"       # 无法归因：按不可信处理，交裁判判定

    @property
    def authorized(self) -> bool:
        """前两类放行，后两类拒绝（报告 §2.1/§2.2）。"""
        return self in (Provenance.USER_SPECIFIED, Provenance.USER_DELEGATED)


class NodeKind(str, Enum):
    """EAG（证据—授权—动作图）节点类型。"""

    USER_REQUEST = "user_request"
    AUTHORIZATION = "authorization"     # A 的某一条授权：(tool, object) 或参数规则
    DELEGATION = "delegation"           # 委托边锚点：字段←来源
    TOOL = "tool"                       # 被授权的工具节点（流程图六类之一）
    OBJECT = "object"                   # 被授权的对象节点（流程图六类之一）
    EVIDENCE = "evidence"               # 带来源标签的证据片段
    ACTION = "action"                   # 规划器提议的动作
    PARAM = "param"                     # 动作的某个参数取值


class EdgeRel(str, Enum):
    """EAG 边类型。"""

    SUPPORTS = "supports"   # 授权/证据 → 参数取值：该值由此支撑
    DERIVES = "derives"     # 委托 → 参数取值：该值由委托查找派生
    PRODUCES = "produces"   # 动作 → 证据：动作产生的新证据
    GRANTS = "grants"       # 用户请求 → 授权：A 由 u 推导
    DELEGATES = "delegates" # 用户请求 → 委托：用户指定了委托


@dataclass(frozen=True)
class EvidenceItem:
    """一条带来源标签的证据片段（工具返回被切分后的产物）。"""

    id: str
    source: str            # 例如 "inbox:msg-42"、"browser:https://..."
    trust: Trust
    text: str
    fields: Mapping[str, str] = field(default_factory=dict)
    #: 这份证据是不是"用户点名要读的资源"产生的（例如请求里写着那个网址/文件）。
    #: 是的话，它的内容属于用户委托的内容，摘要/转发它不算注入。
    authorized: bool = False
    #: 产生这条证据的工具名（如 get_channels），用于识别"清单类"读取。
    producer: str = ""

    def __str__(self) -> str:  # pragma: no cover
        return f"<{self.source} {self.trust.value}> {self.text[:60]}"


@dataclass(frozen=True)
class ToolSpec:
    """工具的静态签名。object_param 指向"作用对象"参数（如收件人）。"""

    name: str
    params: tuple[str, ...]
    object_param: str | None = None
    object_class: str = "object"     # O 中的对象类别名，如 "recipient"、"file"
    side_effect: bool = True
    read_only: bool = False

    def object_of(self, args: Mapping[str, Any]) -> Any:
        if self.object_param is None:
            return None
        return args.get(self.object_param)


@dataclass(frozen=True)
class Action:
    """规划器提议的一个动作。"""

    id: str
    tool: str
    args: Mapping[str, Any]
    intent: str = ""          # 规划器自述意图：只进审计日志，绝不进裁判上下文
    evidence_ids: tuple[str, ...] = ()   # 该动作引用了哪些证据（ΔG 的输入）

    def signature(self) -> str:
        parts = [f"{k}={self.args[k]!r}" for k in sorted(self.args)]
        return f"{self.tool}({', '.join(parts)})"


@dataclass(frozen=True)
class ToolResult:
    """一次工具执行的结果。raw 会按来源切成证据。"""

    tool: str
    text: str
    fields: Mapping[str, str] = field(default_factory=dict)
    ok: bool = True
    error: str | None = None


@dataclass(frozen=True)
class Attribution:
    """某个参数取值的归因结果。"""

    param: str
    value: str
    provenance: Provenance
    evidence_ids: tuple[str, ...] = ()
    note: str = ""

    @property
    def authorized(self) -> bool:
        return self.provenance.authorized


@dataclass(frozen=True)
class Decision:
    """动作审核结论（可审计）。"""

    stage: str                 # "fpr" | "precheck" | "judge" | "output"
    allowed: bool
    reasons: tuple[str, ...] = ()
    detail: Mapping[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.allowed
