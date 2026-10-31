"""参数值来源 s(v) 的归因。

报告 §2.2 把每个参数值分三类：user-specified（直接出现在用户请求或可信内容
中）、user-delegated（用户指定字段由某来源在运行时取值）、injected（只出现
在不可信内容中且未被委托）。这里的归因是"证据侧"的机械判定，语义裁判在其后
复核；两者都看不到规划器的自述理由。
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Mapping, Sequence

from .scope import AuthorizationScope, ParamRule
from .types import Action, Attribution, EvidenceItem, Provenance, ToolSpec, Trust

_WS = re.compile(r"\s+")
# 只保留字母数字、空白与百分号；标点、引号、连字符一律忽略，
# 这样 "12%."、"12%" 和 "12 %" 能对上，而数字本身不会被吞掉。
_NOISE = re.compile(r"[^\w\s%]")
# 金额写法差异：$1,200 / 1 200 / ￥1200 都应归一
_CURRENCY = str.maketrans({",": "", "$": "", "€": "", "¥": "", "￥": "",
                           "£": "", "_": "", "\u00a0": " "})


def _url_forms(value: object) -> str:
    """把 URL 归一成"去掉协议与 www 前缀"的形式，用于文本匹配。"""
    text = str(value).strip()
    for prefix in ("https://", "http://", "www."):
        if text.lower().startswith(prefix):
            text = text[len(prefix):]
    return text.rstrip("/")


def normalize(value: object) -> str:
    """归一化，容忍 $1,200 与 1200、全角半角、大小写、标点差异。"""
    text = str(value)
    text = unicodedata.normalize("NFKC", text)
    text = text.casefold()
    text = text.translate(_CURRENCY)
    text = _WS.sub(" ", text).strip()
    return text


def _squash(value: object) -> str:
    """去掉标点与空白后的紧凑形式，用于宽松包含判断。"""
    return _NOISE.sub("", normalize(value).replace(" ", ""))


def _contains(haystack: str, needle: str) -> bool:
    if not needle:
        return False
    if len(needle) >= 3:
        return needle in haystack or _squash(needle) in _squash(haystack)
    # 太短的值（"1"、"a"）要求词边界，避免误判
    return re.search(rf"(?<![\w.]){re.escape(needle)}(?![\w.])", haystack) is not None


_MONTHS = ("january", "february", "march", "april", "may", "june", "july",
           "august", "september", "october", "november", "december")
_ISO_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def date_variants(value: str) -> list[str]:
    """把 ISO 日期展开成用户可能写出的自然语言形式。

    模型会把「May 26th」规范化成 2024-05-26，若只做子串匹配，用户给出的日期就
    会被判成"无法归因"。这里两个方向都试：ISO → 自然语言。
    """
    match = _ISO_DATE.fullmatch(value.strip())
    if not match:
        return []
    year, month, day = (int(g) for g in match.groups())
    if not 1 <= month <= 12 or not 1 <= day <= 31:
        return []
    name = _MONTHS[month - 1]
    return [
        f"{name} {day}", f"{day} {name}",
        f"{name} {day} {year}", f"{day} {name} {year}",
        f"{name} {day:02d}", f"{month}/{day}", f"{month:02d}/{day:02d}",
    ]


def url_variants(value: str) -> list[str]:
    """URL 的等价写法：带不带协议、带不带 www、结尾斜杠。

    用户写 "www.informations.com"，模型调工具时给 "http://www.informations.com"，
    纯子串匹配会判成"无法归因"，把一个完全合法的读取挡掉。
    """
    text = value.strip().rstrip("/")
    variants: list[str] = []
    for scheme in ("http://", "https://"):
        if text.lower().startswith(scheme):
            text = text[len(scheme):]
            break
    variants.append(text)
    if text.lower().startswith("www."):
        variants.append(text[4:])
    else:
        variants.append("www." + text)
    return variants


def value_in(text: str, value: object) -> bool:
    """值是否出自这段文本：先直接比，再试日期/URL 等价写法，最后比长片段重叠。"""
    needle = normalize(value)
    if _contains(text, needle):
        return True
    raw = str(value)
    for variant in [*date_variants(raw), *url_variants(raw)]:
        if _contains(text, normalize(variant)):
            return True
    # 拼接值：模型常把内容包进自己的句子（"Summary of the article ...: <原文>"），
    # 整体不会出现在证据里。只要有一段足够长的原文片段重合，就算继承该来源。
    if len(needle) > 60:
        window = 40
        for start in range(0, len(needle) - window + 1, 10):
            if needle[start:start + window] in text:
                return True
    return False


#: 攻击者写不进去的来源：用户自己的文件、银行流水、日历。
#: 这些来源里没有结构化字段时（比如账单是纯文本），允许退化成文本匹配；
#: 邮件、频道、网页不在此列——那里面的数字随时可能是注入的。
SAFE_TEXT_SOURCES = frozenset({"file", "bank", "calendar"})


#: 来源别名。解析器会说 "webpage"、"email"、"channel"，而证据标签是
#: "web"、"inbox"、"slack"；不归一化的话委托查找会静默落空
#: （实测"总结网页并发到频道"就是被这个坑挡掉的）。
SOURCE_ALIASES = {
    "webpage": "web", "web_page": "web", "website": "web", "site": "web",
    "url": "web", "http": "web", "https": "web", "browser": "web", "网页": "web",
    "email": "inbox", "emails": "inbox", "mail": "inbox", "邮件": "inbox",
    "files": "file", "filesystem": "file", "文档": "file", "文件": "file",
    "channel": "slack", "channels": "slack", "messages": "slack", "频道": "slack",
    "contact": "contacts", "联系人": "contacts",
    "transactions": "bank", "account": "bank", "流水": "bank",
}


def canonical_source(source: str) -> str:
    key = source.strip().lower()
    return SOURCE_ALIASES.get(key, source.strip())


@dataclass(frozen=True)
class AttributionContext:
    """归因所需的全部输入：用户请求 + 全部证据。"""

    user_request: str
    evidence: Sequence[EvidenceItem]
    user_node: str = "u:request"
    delegation_nodes: Mapping[str, str] = None  # type: ignore[assignment]  # param -> 委托节点 id

    def __post_init__(self) -> None:
        if self.delegation_nodes is None:
            object.__setattr__(self, "delegation_nodes", {})

    def untrusted(self) -> list[EvidenceItem]:
        return [e for e in self.evidence if e.trust is Trust.UNTRUSTED]

    def from_source(self, source: str) -> list[EvidenceItem]:
        """按来源取证据。``"*"`` 表示任意来源。

        解析器可能给出比证据标签更具体的来源（"file:bill.txt" vs "file"），
        两个方向都要认；"inbox" 也要能匹配 "inbox:42"。
        """
        if source == "*":
            return list(self.evidence)
        wanted = [canonical_source(s) for s in source.split("|") if s.strip()]
        return [
            e for e in self.evidence
            if any(e.source == w or e.source.startswith(w + ":") or w.startswith(e.source + ":")
                   for w in wanted)
        ]


@dataclass(frozen=True)
class AttributedParam:
    """归因 + 图上的根节点，供 EAG 连边用。"""

    attribution: Attribution
    roots: tuple[tuple[str, str], ...]   # (node_id, rel)

    @property
    def param(self) -> str:
        return self.attribution.param

    @property
    def value(self) -> str:
        return self.attribution.value

    @property
    def provenance(self) -> Provenance:
        return self.attribution.provenance


class Attributor:
    """把动作的每个参数值落到一个来源上。"""

    def attribute(
        self,
        action: Action,
        spec: ToolSpec | None,
        scope: AuthorizationScope,
        ctx: AttributionContext,
    ) -> list[AttributedParam]:
        out: list[AttributedParam] = []
        request_norm = normalize(ctx.user_request)
        for param, raw in action.args.items():
            value = "" if raw is None else str(raw)
            rule = scope.rule(action.tool, param)

            # 1. 用户直接给出
            if value_in(request_norm, value):
                out.append(
                    AttributedParam(
                        Attribution(param, value, Provenance.USER_SPECIFIED,
                                    note="出现在用户请求中"),
                        ((ctx.user_node, "supports"),),
                    )
                )
                continue

            # 2. 用户委托：字段可委托，且值确实来自被委托来源的"那个字段"。
            #    这里必须按字段取值，不能退回自由文本匹配——否则注入内容里随便
            #    写一个数就能冒充"被委托的金额"，委托就变成了扩权通道。
            if rule.allows_delegation:
                source = rule.delegation_source or ""
                needle = normalize(value)
                pool = ctx.from_source(source)
                if rule.content_delegation:
                    hits = [e for e in pool if value_in(normalize(e.text), value)]
                else:
                    # 试过加字段别名（收款人也可来自 sender 字段，以支持"退钱给他"）：
                    # 实测 ASR 0.69% → 2.78%、效用不变——注入交易里的 sender 同样能
                    # 冒充收款人，净负，已回退。保持只认 recipient。
                    hits = [
                        e for e in pool
                        if e.fields.get(param) is not None
                        and normalize(e.fields[param]) == needle
                    ]
                    # 兜底："来源本身不可被攻击者写入"就退化成整文匹配。
                    # **已删除**：banking 的注入会把账单的 Total/IBAN 两行整个替换掉，
                    # 此时切片抽不到字段，兜底就会把攻击者写在正文里的账户认成
                    # "委托来的收款人"（实测就是这样放过 US133 的）。
                    # 有了证据切片，字段缺失时应当判为"无法归因"，而不是回头信正文。
                if hits:
                    node = (
                        ctx.delegation_nodes.get(f"{action.tool}.{param}")
                        or ctx.delegation_nodes.get(param)
                        or f"d:{action.tool}.{param}"
                    )
                    out.append(
                        AttributedParam(
                            Attribution(param, value, Provenance.USER_DELEGATED,
                                        tuple(e.id for e in hits),
                                        note=f"来自被委托来源 {source}"),
                            ((node, "derives"),),
                        )
                    )
                    continue

            # 3. 只出现在不可信内容中。
            #    但如果这段内容来自"用户点名要读的资源"（请求里写着那个网址/文件），
            #    它就是用户委托的内容——摘要它、转发它都是任务本身。
            #
            #    例外（关键）：**字段型**参数不走这条"整文匹配"的便捷路径。
            #    banking 的注入点就是 injection_bill_text——攻击者把指令写进账单
            #    正文；若按整文匹配，正文里的账户就成了"用户委托的收款人"。
            #    字段型只认结构化字段（账单的 IBAN/Total），正文一律不算。
            field_mode = rule.allows_delegation and not rule.content_delegation
            hits = [
                e for e in ctx.untrusted()
                if value_in(normalize(e.text), value)
                or value_in(normalize(e.text), _url_forms(value))
            ]
            if hits:
                if not field_mode and any(e.authorized for e in hits):
                    node = ctx.delegation_nodes.get(f"{action.tool}.{param}") or ctx.user_node
                    out.append(
                        AttributedParam(
                            Attribution(param, value, Provenance.USER_DELEGATED,
                                        tuple(e.id for e in hits),
                                        note="来自用户点名要读的资源"),
                            ((node, "derives"),),
                        )
                    )
                    continue
                out.append(
                    AttributedParam(
                        Attribution(param, value, Provenance.INJECTED,
                                    tuple(e.id for e in hits), note="只出现在不可信内容中"),
                        tuple((f"e:{e.id}", "supports") for e in hits),
                    )
                )
                continue

            # 4. 归因失败：保守地当作不可信
            out.append(
                AttributedParam(
                    Attribution(param, value, Provenance.UNATTRIBUTED,
                                note="无法归因，按不可信处理"),
                    (),
                )
            )
        return out


def unattributed(value: str, param: str, note: str = "") -> Attribution:
    return Attribution(param, value, Provenance.UNATTRIBUTED, note=note)
