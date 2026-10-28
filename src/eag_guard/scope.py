"""授权范围 A = (T, O, P) 的表示与推导。

报告 §2.1：系统只依据用户请求推导授权范围，明确允许使用的工具、允许作用的
对象以及每个参数值的来源；A 只由 u 推导，不读工具返回。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Protocol, Sequence

from .types import Provenance, ToolSpec


@dataclass(frozen=True)
class ParamRule:
    """P 的一条：某工具某参数允许的来源。

    mode="field"   字段型委托：取值必须来自证据的结构化字段（收款人、金额）。
                   这类值最危险，绝不接受自由文本匹配。
    mode="content" 内容型委托：用户要求"转发/摘要这段内容"，取值本来就是一段
                   不可信文本，此时允许按内容匹配。
    """

    name: str
    allow: frozenset[Provenance] = frozenset(
        {Provenance.USER_SPECIFIED, Provenance.USER_DELEGATED}
    )
    delegable: bool = False
    delegation_source: str | None = None   # 委托查找的来源标签，如 "inbox"
    mode: str = "field"

    @property
    def allows_delegation(self) -> bool:
        return self.delegable and self.delegation_source is not None

    @property
    def content_delegation(self) -> bool:
        return self.mode == "content"

    def permits(self, provenance: Provenance) -> bool:
        return provenance in self.allow


def is_lookalike(candidate: str, allowed: str) -> bool:
    """候选域名是否在仿冒某个授权域名（授权域名是它的真子串但不相等）。

    典型：`www.true-informations.com` 仿冒 `www.informations.com`——
    攻击者常用加前缀/后缀的方式做近似域名。
    """
    a, b = normalize_object(candidate), normalize_object(allowed)
    if not a or not b or a == b:
        return False
    return b in a or a in b


def normalize_object(value: object) -> str:
    """对象取值的规范化：去协议、去 www.、去尾斜杠、统一小写。"""
    text = str(value).strip().casefold().rstrip("/")
    for prefix in ("http://", "https://"):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    if text.startswith("www."):
        text = text[4:]
    return text


@dataclass(frozen=True)
class AuthorizationScope:
    """A = (T, O, P)。"""

    tools: frozenset[str]
    objects: Mapping[str, frozenset[str]] = field(default_factory=dict)
    params: Mapping[str, Mapping[str, ParamRule]] = field(default_factory=dict)
    request_text: str = ""
    read_only: bool = False           # 只读策略：禁止一切有副作用的动作
    notes: tuple[str, ...] = ()

    # ------------------------------------------------------------------ 判定
    def tool_allowed(self, tool: str) -> bool:
        return tool in self.tools

    def object_allowed(self, tool: str, value: object, spec: ToolSpec | None) -> bool:
        """对象是否在 O 内。列表参数要求每个元素都在白名单里。

        比较前做归一化：URL 的协议前缀、www.、结尾斜杠与大小写都不该影响判定。
        `www.x.com` 与 `http://www.X.com/` 是同一个对象——按字符串精确比会
        把用户自己给出的 URL 判成越权（实测过）。
        """
        if value is None or spec is None or spec.object_param is None:
            return True
        allowed = self.objects.get(spec.object_class)
        if allowed is None:
            return True   # 该域未声明对象白名单：交给参数来源判定
        pool = {normalize_object(a) for a in allowed}
        if spec.object_class in {"url", "link"}:
            if any(is_lookalike(str(value), str(a)) for a in allowed):
                return False
        if isinstance(value, (list, tuple, set)):
            return all(normalize_object(v) in pool for v in value) if value else True
        return normalize_object(value) in pool

    def is_lookalike_object(self, value: object, spec: ToolSpec | None) -> bool:
        """作用对象是否是某个授权对象的仿冒（仅对 URL 类有意义）。"""
        if value is None or spec is None or spec.object_class not in {"url", "link"}:
            return False
        allowed = self.objects.get(spec.object_class) or ()
        return any(is_lookalike(str(value), str(a)) for a in allowed)

    def rule(self, tool: str, param: str) -> ParamRule:
        by_tool = self.params.get(tool, {})
        if param in by_tool:
            return by_tool[param]
        return ParamRule(param)

    def delegations(self) -> list[ParamRule]:
        return [
            rule
            for rules in self.params.values()
            for rule in rules.values()
            if rule.allows_delegation
        ]

    # ------------------------------------------------------------------ 展示
    def describe(self) -> str:
        lines = [
            "允许的工具：" + (", ".join(sorted(self.tools)) or "（无）"),
        ]
        for klass, values in sorted(self.objects.items()):
            lines.append(f"允许的{klass}：" + (", ".join(sorted(values)) or "（无）"))
        for tool, rules in sorted(self.params.items()):
            for name, rule in sorted(rules.items()):
                if rule.allow == frozenset(Provenance):
                    # untargeted 委托：来源不预先限定。若这里写成"只能由用户
                    # 直接指定"，裁判会照字面否掉所有运行时选出的值（实测过）。
                    lines.append(f"参数 {tool}.{name}：来源不预先限定，由裁判按用户意图判断")
                elif rule.allows_delegation:
                    lines.append(f"参数 {tool}.{name}：允许由 {rule.delegation_source} 运行时取值")
                else:
                    lines.append(f"参数 {tool}.{name}：只能由用户直接指定")
        if self.read_only:
            lines.append("策略：只读，禁止产生副作用的动作")
        for note in self.notes:
            lines.append("说明：" + note)
        return "\n".join(lines)


class ScopeParser(Protocol):
    """把用户请求解析成 A。实现可以是规则，也可以是 LLM。"""

    def parse(self, request: str, tools: Sequence[ToolSpec]) -> AuthorizationScope: ...


# --------------------------------------------------------------------------- 规则解析


_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_HANDLE = re.compile(r"@[A-Za-z0-9_]{2,}")
_PATH = re.compile(r"(?:[\w-]+/)+[\w.-]+\.\w+|\b[\w-]+\.(?:txt|csv|md|json|pdf|docx)\b")
_MONEY = re.compile(r"(?:US)?\$\s?\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s?(?:美元|元)")

# 委托线索：用户用"那里/其中/所列/附件中"等措辞把某字段指向运行时来源
_DELEGATION_CUES = (
    "那里", "其中", "所列", "里面", "附件中", "邮件中", "正文中", "表中",
    "listed", "therein", "in the email", "in the file", "from the inbox",
)


@dataclass(frozen=True)
class DomainPack:
    """一个域的词汇表：工具名、对象类别、参数默认规则、来源标签。"""

    name: str
    tools: Mapping[str, ToolSpec]
    object_class: str = "recipient"
    delegable_params: Mapping[str, str] = field(default_factory=dict)  # param -> source
    lexicon: Mapping[str, tuple[str, ...]] = field(default_factory=dict)  # tool -> 触发词
    structured_params: frozenset[str] = frozenset()   # 走字段型委托的参数


class RuleScopeParser:
    """启发式解析器：够用就好，真实实验里换成 LLM 解析器。

    只在报告意义上做一件事：从用户请求里抽出 T/O/P，绝不读工具返回。
    """

    def __init__(self, pack: DomainPack) -> None:
        self.pack = pack

    def parse(self, request: str, tools: Sequence[ToolSpec] | None = None) -> AuthorizationScope:
        available = tools or list(self.pack.tools.values())
        names = {t.name for t in available}
        # 先按辞书里的触发词识别工具，再退回到工具名直接出现。
        mentioned = {
            name for name, words in self.pack.lexicon.items()
            if name in names and any(w.lower() in request.lower() for w in words)
        }
        mentioned |= {n for n in names if n in request}
        # 用户没点名工具时，只默认放行只读工具（写入类必须被点名）。
        if not mentioned:
            mentioned = {n for n, t in self.pack.tools.items() if t.read_only}
        emails = set(_EMAIL.findall(request))
        handles = {h.lower() for h in _HANDLE.findall(request)} - {"@example"}
        paths = set(_PATH.findall(request))
        objects: dict[str, set[str]] = {}
        if emails:
            objects["recipient"] = {e.lower() for e in emails}
        if handles:
            objects.setdefault("recipient", set()).update(handles)
        if paths:
            objects["file"] = set(paths)

        delegated = bool(re.search("|".join(_DELEGATION_CUES), request, re.IGNORECASE))
        params: dict[str, dict[str, ParamRule]] = {}
        for tool_name in mentioned:
            spec = self.pack.tools.get(tool_name)
            if spec is None:
                continue
            rules: dict[str, ParamRule] = {}
            for param in spec.params:
                source = self.pack.delegable_params.get(param)
                delegated_here = bool(source) and delegated
                # 用户已经在请求里点名了对象（收件人/文件），就不再把对象交给委托
                if delegated_here and param == spec.object_param and (emails or handles or paths):
                    delegated_here = False
                if delegated_here:
                    mode = "field" if param in self.pack.structured_params else "content"
                    rules[param] = ParamRule(param, delegable=True,
                                             delegation_source=source, mode=mode)
                else:
                    rules[param] = ParamRule(param)
            params[tool_name] = rules

        return AuthorizationScope(
            tools=frozenset(mentioned),
            objects={k: frozenset(v) for k, v in objects.items()},
            params=params,
            request_text=request,
        )


def effective_objects(scope: AuthorizationScope, tool: str, spec: ToolSpec) -> frozenset[str] | None:
    return scope.objects.get(spec.object_class)


def scope_from_parts(
    tools: Iterable[str],
    objects: Mapping[str, Iterable[str]] | None = None,
    params: Mapping[str, Mapping[str, ParamRule]] | None = None,
    request_text: str = "",
) -> AuthorizationScope:
    """构造 A 的便捷入口（供测试与离线 mock 使用）。"""
    return AuthorizationScope(
        tools=frozenset(tools),
        objects={k: frozenset(v) for k, v in (objects or {}).items()},
        params={t: dict(rules) for t, rules in (params or {}).items()},
        request_text=request_text,
    )
