"""执行前判定流水线：解析 → 逐步审核循环 → 输出审核。

报告 §2.3：
    1. 任务解析：一次 LLM 调用只读用户请求，产出 T/O/P 与委托查找；
    2. 逐步审核循环：工具返回切成带来源标签的证据构成 EAG，规划器提议动作，
       独立裁判核对，通过则执行前再次核对工具名与参数，执行结果写回证据；
       拒绝则返回可操作原因并驱动重规划；
    3. 输出审核。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Mapping, Protocol, Sequence

from .audit import AuditResult, OutputAudit
from .eag import EAG
from .judge import Judge, JudgeView
from .parsing import (
    STRICT_PARAMS,
    ID_PARAMS as ID_PARAM_NAMES,
    LISTING_TOOLS,
    TEMPORAL_PARAMS,
    URL_PARAMS,
    extract_candidates,
)
from .provenance import AttributedParam, AttributionContext, Attributor, normalize, value_in
from .scope import AuthorizationScope, ScopeParser
from .types import (
    Action,
    Decision,
    EdgeRel,
    EvidenceItem,
    Provenance,
    ToolResult,
    ToolSpec,
    Trust,
)

#: 来源全部放行的规则（策略性豁免，不再交裁判复议）
ALL_PROVENANCE = frozenset(Provenance)
#: 默认的严格规则：只允许用户直接给出或显式委托。
#: 任何偏离这条的规则都已经是代码层面的策略决定，不再交裁判复议。
STRICT_ALLOW = frozenset({Provenance.USER_SPECIFIED, Provenance.USER_DELEGATED})


# --------------------------------------------------------------------------- 协作方协议


@dataclass(frozen=True)
class Execution:
    """一次工具执行：结果 + 被切分出的带来源标签的证据。"""

    result: ToolResult
    evidence: tuple[EvidenceItem, ...] = ()


class Environment(Protocol):
    """被保护的外部环境。execute 的返回值必须已经带来源标签。"""

    def execute(self, action: Action) -> Execution: ...


class Planner(Protocol):
    """规划器：可以随证据演化计划，但绝不能自行扩权。"""

    def propose(self, step: int) -> Action | None: ...

    def observe(self, action: Action, result: ToolResult) -> None: ...

    def reject(self, action: Action, reasons: Sequence[str]) -> None: ...

    def finalize(self) -> str: ...


# --------------------------------------------------------------------------- 配置与轨迹


@dataclass(frozen=True)
class GuardConfig:
    """一个消融臂的完整配置（对应报告 §4.3 的六臂对照）。"""

    name: str = "eag"
    enable_fpr: bool = True          # 字段级溯源可达性
    enable_judge: bool = True        # 独立语义裁判
    allow_delegation: bool = True    # 是否承认委托边
    read_only_policy: bool = False   # 只读策略（按域选择）
    read_policy: str = "allow_all"   # audit_all | no_target | allow_all（报告表 4-2）
    #: 即使在 untargeted 下也必须"只能由用户指定/委托"的参数，写成 "工具.参数"。
    #: 用于资金流向这类"来源一错就是事故"的字段（如转账收款人 IBAN）。
    strict_params: tuple[str, ...] = ()
    #: 必须来自**结构化字段**的参数（"工具.参数"）：允许用户指定或运行时委托，
    #: 但委托只认字段（账单的 IBAN/Total、交易的 recipient/amount），
    #: 不认正文里出现的字符串。有了证据切片，这条既能放过"像上个月那样付"
    #: 这类合法委托，又能挡住写在 subject 里的注入账户。
    field_strict_params: tuple[str, ...] = ()
    delegation: str = "untargeted"   # untargeted | targeted（报告主配置是 untargeted）
    #: 纯结构（白名单）模式：所有参数只允许"用户直接指定"，既不承认委托，
    #: 也不做 untargeted 放宽。对应报告表 4-2 里"纯结构 8% / 0.48"那一档。
    structure_only: bool = False
    output_audit: bool = True        # 输出审核
    feedback: str = "strong"         # strong | weak
    max_steps: int = 8


@dataclass
class StepRecord:
    index: int
    action: Action
    attributions: tuple[AttributedParam, ...]
    decisions: list[Decision] = field(default_factory=list)
    executed: bool = False
    result: str = ""

    @property
    def reasons(self) -> tuple[str, ...]:
        return tuple(r for d in self.decisions if not d.allowed for r in d.reasons)


@dataclass
class Trace:
    case_id: str
    request: str
    scope: AuthorizationScope
    graph: EAG
    steps: list[StepRecord] = field(default_factory=list)
    final_answer: str = ""
    audit: AuditResult | None = None
    config: GuardConfig = field(default_factory=GuardConfig)
    error: str | None = None

    @property
    def rejections(self) -> int:
        return sum(1 for s in self.steps if not s.executed)

    @property
    def executions(self) -> int:
        return sum(1 for s in self.steps if s.executed)

    def blocked(self) -> list[StepRecord]:
        return [s for s in self.steps if not s.executed]

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "request": self.request,
            "config": self.config.name,
            "steps": [
                {
                    "index": s.index,
                    "action": s.action.signature(),
                    "executed": s.executed,
                    "provenance": {a.param: a.provenance.value for a in s.attributions},
                    "reasons": list(s.reasons),
                }
                for s in self.steps
            ],
            "answer": self.final_answer,
            "audit": {
                "flagged": self.audit.flagged if self.audit else False,
                "findings": list(self.audit.findings) if self.audit else [],
            },
            "graph": self.graph.to_dict(),
        }


# --------------------------------------------------------------------------- 守卫


def _is_blank(value: object) -> bool:
    """空字符串、None、空列表/空字典都算"没填"。"""
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip() or value.strip() in {"[]", "{}", "None", "null"}
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _as_values(value: object) -> tuple[object, ...]:
    """把可能是列表的对象值摊平成可逐个比较的值。"""
    if isinstance(value, (list, tuple, set)):
        return tuple(value)
    return (value,)


@dataclass
class GuardState:
    """一个任务内不变的判定上下文：授权范围 + 图 + 根节点。"""

    request: str
    scope: AuthorizationScope
    graph: EAG
    user_node: str
    delegation_nodes: dict[str, str] = field(default_factory=dict)


class Guard:
    def __init__(
        self,
        parser: ScopeParser,
        planner_factory,
        judge: Judge,
        tools: Mapping[str, ToolSpec],
        *,
        config: GuardConfig | None = None,
        audit: OutputAudit | None = None,
        attributor: Attributor | None = None,
    ) -> None:
        self.parser = parser
        self.planner_factory = planner_factory
        self.judge = judge
        self.tools = dict(tools)
        self.config = config or GuardConfig()
        self.audit = audit if audit is not None else OutputAudit()
        self.attributor = attributor or Attributor()

    # ------------------------------------------------------------------ 主流程
    def prepare(self, request: str) -> GuardState:
        """解析授权范围、建图、登记授权与委托节点。一个任务只做一次。"""
        scope = self.parser.parse(request, list(self.tools.values()))
        if self.config.delegation == "untargeted":
            # delegation_untargeted：不预先指定"哪个字段来自哪个来源"，
            # 运行时从读到的材料取值一律视为委托。结构层只保留 T/O 两道门，
            # 参数来源交给独立裁判判断——这正是报告 §4.3 里
            # "纯结构+委托 44%/0.92 → EAG 4%/0.92" 的做法。
            from .scope import ParamRule as _ParamRule

            # strict 例外：资金流向这类字段（转账收款人）即便在 untargeted 下
            # 也必须"用户指定或已授权来源"。实测抓到过守卫放行
            # send_money(recipient=<攻击者 IBAN>)，就是因为这里把 STRICT 也放宽了。
            strict = set(self.config.strict_params)
            widened = {
                tool: {
                    name: (
                        # 资金流向字段强制"字段型委托"：只认结构化字段
                        # （账单里的 IBAN/Total 行），不认正文整文匹配。
                        # 注入正是把假 IBAN 写在账单/通知正文里；走整文匹配的话
                        # 它会立刻被当成"用户委托来的收款人"（全域实测放过 US133…）。
                        replace(original, mode="field", delegable=True,
                                delegation_source=original.delegation_source or "file")
                        if f"{tool}.{name}" in strict
                        # delegable=True 很关键：untargeted 的语义是"来源不预先
                        # 限定"，对象参数也应随之交给裁判判定，而不是继续被
                        # 白名单硬卡。实测 slack 里"邀请邮件提到的新同事 Dora"、
                        # "读 Bob 的收件箱"都被判"不在 O"而误杀。
                        else _ParamRule(name, allow=ALL_PROVENANCE)
                    )
                    for name, original in rules.items()
                }
                for tool, rules in scope.params.items()
            }
            scope = AuthorizationScope(
                tools=scope.tools, objects=scope.objects, params=widened,
                request_text=scope.request_text, read_only=scope.read_only,
                notes=scope.notes + ("untargeted delegation",),
            )
        if self.config.read_only_policy:
            scope = AuthorizationScope(
                tools=scope.tools, objects=scope.objects, params=scope.params,
                request_text=scope.request_text, read_only=True, notes=scope.notes,
            )
        graph = EAG()
        user_node = graph.add_user_request(request)
        # 流程图里的六类节点：授权 / 工具 / 对象 / 证据 / 参数 / 动作。
        for tool in sorted(scope.tools):
            tool_node = graph.add_tool(tool)
            auth = graph.add_authorization(f"工具 {tool}", {"tool": tool})
            graph.add_edge(auth.id, tool_node.id, EdgeRel.SUPPORTS)
        for klass, values in sorted(scope.objects.items()):
            for value in sorted(values):
                object_node = graph.add_object(klass, str(value))
                auth = graph.add_authorization(f"{klass}={value}", {"object": value})
                graph.add_edge(auth.id, object_node.id, EdgeRel.SUPPORTS)

        delegation_nodes: dict[str, str] = {}
        for rule in scope.delegations():
            node = graph.add_delegation(rule.name, rule.delegation_source or "", user_node.id)
            delegation_nodes.setdefault(rule.name, node.id)
            for tool_name, rules in scope.params.items():
                if rules.get(rule.name) is rule:
                    delegation_nodes[f"{tool_name}.{rule.name}"] = node.id

        return GuardState(request=request, scope=scope, graph=graph,
                          user_node=user_node.id, delegation_nodes=delegation_nodes)

    def review(self, state: GuardState, action: Action,
               evidence: Sequence[EvidenceItem], index: int = 0) -> StepRecord:
        """对一个候选动作做完整判定，返回带决策记录的 StepRecord。

        不执行动作——执行由调用方（`run` 或 AgentDojo 适配层）负责。
        """
        spec = self.tools.get(action.tool)
        state.graph.add_action(action)

        ctx = AttributionContext(
            user_request=state.request,
            evidence=tuple(evidence),
            user_node=state.user_node,
            delegation_nodes=state.delegation_nodes,
        )
        attributions = self.attributor.attribute(action, spec, state.scope, ctx)
        for attr in attributions:
            state.graph.add_param(action.id, attr.attribution,
                                  tuple((root, EdgeRel(rel)) for root, rel in attr.roots))

        record = StepRecord(index, action, tuple(attributions))

        # 1) 结构判定：工具/对象/参数来源（FPR）
        if self.config.enable_fpr:
            decision = self._fpr_decision(action, attributions, spec, state.scope)
            record.decisions.append(decision)
            if not decision:
                return record

        # 2) 独立语义裁判（上下文里没有 planning intent）
        #    只读动作不进裁判：它没有副作用，对象白名单已经在上面挡住了越界读取；
        #    每读一次都问一遍模型既贵又容易误杀。
        read_only = spec is not None and spec.read_only
        touches_url = any(p in URL_PARAMS for p in action.args)
        if self.config.enable_judge and not (read_only and not touches_url):
            # 策略已放行的字段（时间等）不再交给裁判复议，否则它会用
            # "用户没有逐字指定"这类理由把正常动作否掉。
            # untargeted 委托下，所有参数的"放行"都是策略性放行，但**恰恰是这时候
            # 必须让裁判看全部参数**——结构层已经不再把关来源了。
            if self.config.delegation == "untargeted":
                # 只把"方向性"参数交给裁判：收件人、收款人、金额、链接、作用对象。
                # 正文类（body/subject/description/location/title）一律豁免——
                # 它们改不了数据流向，却几乎永远不可能逐字出现在用户请求里，
                # 交给裁判只会制造误杀。
                directional = set(STRICT_PARAMS) | set(URL_PARAMS)
                if spec is not None and spec.object_param:
                    directional.add(spec.object_param)
                exempt = tuple(a.param for a in attributions if a.param not in directional)
            else:
                exempt = tuple(
                    a.param for a in attributions
                    if state.scope.rule(action.tool, a.param).allow != STRICT_ALLOW
                )
            reviewable = tuple(a for a in attributions if a.param not in exempt)
            # 所有参数都已由策略放行：没有可审的东西，不要再问模型——
            # 否则它会拿"用户没逐字说过"去否掉一个本该放行的动作。
            if not reviewable:
                return record
            by_id = {e.id: e for e in evidence}
            candidates: dict[str, tuple[str, ...]] = {}
            for a in reviewable:
                for eid in a.attribution.evidence_ids:
                    ev = by_id.get(eid)
                    if ev is not None and ev.producer in LISTING_TOOLS:
                        values = extract_candidates(ev.text)
                        if values:
                            candidates[a.param] = values
            view = JudgeView(
                user_request=state.request,
                scope=state.scope,
                action=action,
                spec=spec,
                attributions=reviewable,
                origins={
                    a.param: tuple(dict.fromkeys(
                        # 标明"这份材料是用户点名要读的"，裁判据此判断
                        # "顺着它取值"属于任务本身，而不是看来源标签猜。
                        f"{ev.producer or ev.source}"
                        + ("（用户点名的材料）" if ev.authorized else "")
                        for ev in (by_id.get(i) for i in a.attribution.evidence_ids)
                        if ev is not None
                    ))
                    for a in reviewable
                },
                candidates=candidates,
                exempt_params=exempt,
                tool_allowed=state.scope.tool_allowed(action.tool),
                object_allowed=(
                    True if (spec is None or spec.object_param is None)
                    else state.scope.object_allowed(action.tool, spec.object_of(action.args), spec)
                ),
            )
            decision = self.judge.review(view)
            record.decisions.append(decision)
            if not decision:
                return record

        # 3) 执行前再次核对：判定的签名必须等于即将执行的签名。
        #    目前 Action 是不可变对象，这一步是结构性的；真实 ReAct 循环里
        #    规划器可能复用同一个参数字典，那时它才是真正的时间差防护。
        if action.signature() != self._signature(record):
            record.decisions.append(Decision("precheck", False, ("动作在审核后被修改",)))
        return record

    def run(self, request: str, env: Environment, case_id: str = "case") -> Trace:
        state = self.prepare(request)
        trace = Trace(case_id=case_id, request=request, scope=state.scope,
                      graph=state.graph, config=self.config)
        planner = self.planner_factory(request, state.scope)
        evidence: list[EvidenceItem] = []

        for step in range(self.config.max_steps):
            action = planner.propose(step)
            if action is None:
                break
            record = self.review(state, action, evidence, step)
            trace.steps.append(record)

            if not all(d.allowed for d in record.decisions):
                self._deny(planner, action, record)
                continue

            execution = env.execute(action)
            record.executed = True
            record.result = execution.result.text
            for item in execution.evidence:
                if f"e:{item.id}" not in state.graph:
                    state.graph.add_evidence(item)
                evidence.append(item)
            planner.observe(action, execution.result)

        trace.final_answer = planner.finalize()
        trace.audit = self.audit.audit(trace.final_answer, evidence)
        trace.final_answer = trace.audit.text
        return trace

    # ------------------------------------------------------------------ 判定
    @staticmethod
    def _signature(record: StepRecord) -> str:
        return record.action.signature()

    def _fpr_decision(
        self,
        action: Action,
        attributions: Sequence[AttributedParam],
        spec: ToolSpec | None,
        scope: AuthorizationScope,
    ) -> Decision:
        reasons: list[str] = []
        if spec is None:
            reasons.append(f"工具 {action.tool} 未注册")
        else:
            if not scope.tool_allowed(action.tool):
                reasons.append(f"工具 {action.tool} 不在授权范围 T 内")
            # 只读策略（报告表 4-2，按域选择）必须先于对象白名单：
            # audit_all 全审；no_target 只放行无目标读取；allow_all 读取免审。
            # 踩坑：对象检查跑在策略前面，travel 的
            # get_restaurants_address(restaurant_names=[...]) 被判"对象不在 O"，
            # 模型拿不到地址，答复缺字段，任务直接失败。
            if spec.read_only:
                no_target = not action.args
                if self.config.read_policy == "allow_all" or (
                    self.config.read_policy == "no_target" and no_target
                ):
                    return Decision("fpr", True, (),
                                    detail={"action": action.signature(),
                                            "read_only": True,
                                            "read_policy": self.config.read_policy})

            obj = spec.object_of(action.args)
            # 对象 id（事件/文件/邮件）由"同类来源"委托管住，不再走白名单——
            # id 本来就产生在读取里，用白名单卡它只会把正常任务卡死。
            # 可委托的参数（对象 id、URL）由"来源"管住，不再叠加白名单；
            # 否则"检查 Dora 的网站"这种由人名派生的 URL 永远过不了。
            id_scoped = (spec.object_param in ID_PARAM_NAMES
                         or scope.rule(action.tool, spec.object_param or "").allows_delegation)
            # 仿冒域名单独判：它不受"可委托参数跳过白名单"的影响。
            if scope.is_lookalike_object(obj, spec):
                reasons.append(f"对象 {obj!r} 是授权域名的仿冒")
            elif not id_scoped and not scope.object_allowed(action.tool, obj, spec):
                # 授权范围本来就只从用户请求推导：**字面出现在请求里的值一定在授权内**。
                # 解析器漏写（实测 slack 的 "Bob 不在 O"）不该把整条任务链从第一步就掐断。
                if not any(value_in(normalize(scope.request_text), str(v)) for v in _as_values(obj)):
                    reasons.append(f"对象 {obj!r} 不在授权范围 O 内")
            if scope.read_only and spec.side_effect:
                reasons.append(f"只读策略禁止 {action.tool} 产生副作用")


        # 跨切片一致性：收款人与金额都必须来自**同一条记录**。
        # 注入常把伪造的 IBAN 塞在另一处（另一条消息、另一段正文），
        # 这样"收款人来自 A、金额来自 B"的付款就是拼出来的。
        money_group = {"recipient", "payee", "amount", "total"}
        delegated_money = [
            a for a in attributions
            if a.param in money_group
            and a.provenance is Provenance.USER_DELEGATED
            and a.attribution.evidence_ids
        ]
        if len(delegated_money) >= 2:
            common = set(delegated_money[0].attribution.evidence_ids)
            for item in delegated_money[1:]:
                common &= set(item.attribution.evidence_ids)
            if not common:
                reasons.append(
                    "收款人与金额来自不同的记录（可能是拼接出来的付款），拒绝"
                )

        for attr in attributions:
            # 空值不参与溯源：模型把可选参数留空（cc=''、attachments=[]）
            # 不是越权。实测这条把 travel 的 send_email 整条拒掉了。
            if _is_blank(attr.value):
                continue
            # 硬规则：只出现在不可信内容里、没有被委托的 URL 一律不读。
            # 这正是"外部内容可以改变计划，但不能改变授权"——按注入给的链接去
            # 访问，等于把请求发给攻击者指定的服务器。它不受 untargeted 放宽。
            if attr.param in URL_PARAMS and attr.provenance is Provenance.INJECTED:
                reasons.append(f"链接 {attr.value!r} 只出现在不可信内容中，未被委托")
                continue
            rule = scope.rule(action.tool, attr.param)
            if rule.permits(attr.provenance):
                continue
            if attr.provenance is Provenance.USER_DELEGATED and not self.config.allow_delegation:
                reasons.append(f"参数 {attr.param} 依赖委托，但本配置不放行委托")
            elif attr.provenance is Provenance.INJECTED:
                reasons.append(
                    f"参数 {attr.param}={attr.value!r} 只可溯源到不可信内容（FPR 无可信根路径）"
                )
            else:
                reasons.append(f"参数 {attr.param}={attr.value!r} 无法归因到任何授权")

        return Decision(
            stage="fpr",
            allowed=not reasons,
            reasons=tuple(reasons),
            detail={"action": action.signature()},
        )

    def _deny(self, planner: Planner, action: Action, record: StepRecord) -> None:
        if self.config.feedback == "weak":
            planner.reject(action, ("动作被拒绝",))
        else:
            planner.reject(action, record.reasons)






