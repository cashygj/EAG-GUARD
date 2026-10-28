"""证据—授权—动作图（EAG）与字段级溯源可达性（FPR）。

报告 §2.2：
    图上的判定用字段级溯源可达性（FPR）：从参数节点沿 supports/derives
    回溯，能到达直接授权或委托节点则放行，只到达 untrusted 证据则拒绝。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from .types import (
    Action,
    Attribution,
    EdgeRel,
    EvidenceItem,
    NodeKind,
    Provenance,
    Trust,
)


@dataclass
class Node:
    id: str
    kind: NodeKind
    label: str
    trust: Trust = Trust.TRUSTED
    payload: Mapping[str, object] = field(default_factory=dict)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Node({self.id}, {self.kind.value}, {self.label!r})"


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    rel: EdgeRel


@dataclass(frozen=True)
class FPRResult:
    """一个参数取值的溯源结论。"""

    param: str
    value: str
    trusted_roots: tuple[str, ...]      # 到达的授权/委托/用户请求节点
    untrusted_roots: tuple[str, ...]    # 只到达的不可信证据节点
    allow: bool

    @property
    def reason(self) -> str:
        if self.allow:
            return f"{self.param}={self.value!r} 可溯源到 {', '.join(self.trusted_roots)}"
        if self.untrusted_roots:
            return f"{self.param}={self.value!r} 只可溯源到不可信证据 {', '.join(self.untrusted_roots)}"
        return f"{self.param}={self.value!r} 无可溯源依据（视为不可信）"


class EAG:
    """有向图：节点 + 边。只做记录与回溯，不做策略判断以外的推理。"""

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._out: dict[str, list[Edge]] = {}
        self._in: dict[str, list[Edge]] = {}
        self._seq = 0

    # ------------------------------------------------------------------ 构建
    def _next_id(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}{self._seq}"

    def add_node(self, node: Node) -> Node:
        self._nodes[node.id] = node
        self._out.setdefault(node.id, [])
        self._in.setdefault(node.id, [])
        return node

    def add_edge(self, src: str, dst: str, rel: EdgeRel) -> Edge:
        edge = Edge(src, dst, rel)
        self._out.setdefault(src, []).append(edge)
        self._in.setdefault(dst, []).append(edge)
        return edge

    def add_user_request(self, text: str) -> Node:
        return self.add_node(
            Node(self._next_id("u"), NodeKind.USER_REQUEST, "用户请求", Trust.TRUSTED,
                 {"text": text})
        )

    def add_authorization(self, label: str, payload: Mapping[str, object]) -> Node:
        return self.add_node(
            Node(self._next_id("a"), NodeKind.AUTHORIZATION, label, Trust.TRUSTED, dict(payload))
        )

    def add_tool(self, name: str) -> Node:
        return self.add_node(
            Node(self._next_id("t"), NodeKind.TOOL, f"工具:{name}", Trust.TRUSTED,
                 {"tool": name}))

    def add_object(self, klass: str, value: str) -> Node:
        return self.add_node(
            Node(self._next_id("o"), NodeKind.OBJECT, f"{klass}={value}", Trust.TRUSTED,
                 {"class": klass, "value": value}))

    def add_delegation(self, field_name: str, source: str, authorized_by: str | None = None) -> Node:
        node = self.add_node(
            Node(self._next_id("d"), NodeKind.DELEGATION, f"{field_name}←{source}",
                 Trust.TRUSTED, {"field": field_name, "source": source})
        )
        if authorized_by:
            self.add_edge(authorized_by, node.id, EdgeRel.DELEGATES)
        return node

    def add_evidence(self, item: EvidenceItem) -> Node:
        return self.add_node(
            Node(f"e:{item.id}", NodeKind.EVIDENCE, item.source, item.trust,
                 {"text": item.text, "fields": dict(item.fields)})
        )

    def add_action(self, action: Action) -> Node:
        return self.add_node(
            Node(f"act:{action.id}", NodeKind.ACTION, action.signature(), Trust.TRUSTED,
                 {"tool": action.tool})
        )

    def add_param(self, action_id: str, attribution: Attribution,
                  roots: Iterable[tuple[str, EdgeRel]]) -> Node:
        """登记参数节点，并把它的支撑/派生边接到给定根节点上。"""
        node = self.add_node(
            Node(self._next_id("p"), NodeKind.PARAM, f"{attribution.param}={attribution.value!r}",
                 Trust.TRUSTED, {"value": attribution.value})
        )
        self.add_edge(f"act:{action_id}", node.id, EdgeRel.SUPPORTS)
        for root_id, rel in roots:
            if root_id in self._nodes:
                self.add_edge(root_id, node.id, EdgeRel(rel))
        return node

    # ------------------------------------------------------------------ 查询
    def node(self, node_id: str) -> Node:
        return self._nodes[node_id]

    def __contains__(self, node_id: str) -> bool:
        return node_id in self._nodes

    def nodes_of(self, kind: NodeKind) -> list[Node]:
        return [n for n in self._nodes.values() if n.kind is kind]

    def edges(self) -> list[Edge]:
        return [e for edges in self._out.values() for e in edges]

    # ------------------------------------------------------------------ FPR
    def fpr(self, param_node_id: str) -> FPRResult:
        """字段级溯源可达性：沿 supports/derives 向后回溯到根。"""
        node = self._nodes[param_node_id]
        trusted: list[str] = []
        untrusted: list[str] = []
        seen: set[str] = {param_node_id}
        stack = [param_node_id]
        while stack:
            current = stack.pop()
            for edge in self._in.get(current, []):
                if edge.rel not in (EdgeRel.SUPPORTS, EdgeRel.DERIVES):
                    continue
                src = self._nodes.get(edge.src)
                if src is None or src.id in seen:
                    continue
                seen.add(src.id)
                if src.kind is NodeKind.EVIDENCE:
                    if src.trust is Trust.UNTRUSTED:
                        untrusted.append(src.id)
                    else:
                        trusted.append(src.id)
                elif src.kind in (NodeKind.AUTHORIZATION, NodeKind.DELEGATION,
                                  NodeKind.USER_REQUEST):
                    trusted.append(src.id)
                else:
                    stack.append(src.id)
        allow = bool(trusted)
        return FPRResult(
            param=str(node.payload.get("param", node.label)),
            value=str(node.payload.get("value", "")),
            trusted_roots=tuple(dict.fromkeys(trusted)),
            untrusted_roots=tuple(dict.fromkeys(untrusted)),
            allow=allow,
        )

    def check_attributions(self, action_id: str) -> list[FPRResult]:
        return [
            self.fpr(n.id)
            for n in self._nodes.values()
            if n.kind is NodeKind.PARAM
            and any(e.dst == n.id and e.src == f"act:{action_id}" for e in self._in.get(n.id, []))
        ]

    # ------------------------------------------------------------------ 导出
    def to_dict(self) -> dict:
        return {
            "nodes": [
                {"id": n.id, "kind": n.kind.value, "label": n.label,
                 "trust": n.trust.value, "payload": dict(n.payload)}
                for n in self._nodes.values()
            ],
            "edges": [
                {"src": e.src, "dst": e.dst, "rel": e.rel.value} for e in self.edges()
            ],
        }


def provenance_from_fpr(result: FPRResult) -> Provenance:
    """把 FPR 结论折算回 s(v) 三分类，供裁判与日志使用。"""
    if result.allow:
        return Provenance.USER_SPECIFIED
    if result.untrusted_roots:
        return Provenance.INJECTED
    return Provenance.UNATTRIBUTED
