# -*- coding: utf-8 -*-
"""EAG-Guard 创新点与代码实现全解（源码级）。"""
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
SONG = "宋体"
HEI = "黑体"
MONO = "Consolas"
NAVY = RGBColor(0x16, 0x28, 0x3F)
TEAL = RGBColor(0x0F, 0x76, 0x6E)
GREY = RGBColor(0x5B, 0x6B, 0x7C)
RED = RGBColor(0xC0, 0x39, 0x2B)

doc = Document()
normal = doc.styles["Normal"]
normal.font.name = SONG
normal.font.size = Pt(10.8)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), SONG)
normal.paragraph_format.line_spacing = 1.4
normal.paragraph_format.space_after = Pt(4)

for sec in doc.sections:
    sec.top_margin = Cm(2.0)
    sec.bottom_margin = Cm(2.0)
    sec.left_margin = Cm(2.2)
    sec.right_margin = Cm(2.2)


def _set(run, size, bold=False, color=None, font=SONG):
    run.font.size = Pt(size)
    run.bold = bold
    run.font.name = "Consolas" if font == MONO else "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font if font != MONO else "宋体")
    if color is not None:
        run.font.color.rgb = color


def para(parts, size=10.8, space_before=0, space_after=4):
    par = doc.add_paragraph()
    fmt = par.paragraph_format
    fmt.line_spacing = 1.4
    fmt.space_before = Pt(space_before)
    fmt.space_after = Pt(space_after)
    for text, bold, color, font in parts:
        run = par.add_run(text)
        _set(run, size, bold, color, font)
    return par


def plain(text, size=10.8, color=None, bold=False, space_before=0, space_after=4):
    return para([(text, bold, color, SONG)], size, space_before, space_after)


def h1(text, size=13.2):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(15)
    par.paragraph_format.space_after = Pt(5)
    run = par.add_run(text)
    _set(run, size, True, NAVY, HEI)
    return par


def h2(text, size=11.5):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(9)
    par.paragraph_format.space_after = Pt(3)
    run = par.add_run(text)
    _set(run, size, True, TEAL, HEI)
    return par


def bullet(parts, size=10.3, indent=0.9):
    par = doc.add_paragraph()
    fmt = par.paragraph_format
    fmt.left_indent = Cm(indent)
    fmt.first_line_indent = Cm(-0.42)
    fmt.space_after = Pt(2)
    fmt.line_spacing = 1.36
    run = par.add_run("· ")
    _set(run, size)
    for text, bold, color, font in parts:
        r = par.add_run(text)
        _set(r, size, bold, color, font)
    return par


def code(text, size=8.3, fill="F4F6F8"):
    lines = text.strip("\n").split("\n")
    for i, ln in enumerate(lines):
        par = doc.add_paragraph()
        fmt = par.paragraph_format
        fmt.left_indent = Cm(0.55)
        fmt.space_before = Pt(2 if i == 0 else 0)
        fmt.space_after = Pt(0)
        fmt.line_spacing = 1.12
        run = par.add_run(ln if ln else " ")
        _set(run, size, False, RGBColor(0x22, 0x30, 0x3D), MONO)
        pPr = par._p.get_or_add_pPr()
        shd = pPr.makeelement(qn("w:shd"), {})
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), fill)
        pPr.append(shd)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def shade_cell(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.makeelement(qn("w:shd"), {})
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def table(headers, rows, widths, size=8.8):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblPr = t._tbl.tblPr
    layout = tblPr.makeelement(qn("w:tblLayout"), {})
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        _set(r, size, True, RGBColor(0xFF, 0xFF, 0xFF), HEI)
        shade_cell(c, "16404D")
    trPr = t.rows[0]._tr.get_or_add_trPr()
    trPr.append(trPr.makeelement(qn("w:tblHeader"), {}))
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            _set(r, size)
    for row in t.rows:
        trPr = row._tr.get_or_add_trPr()
        trPr.append(trPr.makeelement(qn("w:cantSplit"), {}))
    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w)
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


# ==================================================================
par = doc.add_paragraph()
par.alignment = WD_ALIGN_PARAGRAPH.CENTER
par.paragraph_format.space_after = Pt(3)
r = par.add_run("EAG-Guard 创新点与代码实现全解")
_set(r, 18.5, True, NAVY, HEI)

par = doc.add_paragraph()
par.alignment = WD_ALIGN_PARAGRAPH.CENTER
par.paragraph_format.space_after = Pt(10)
r = par.add_run("从授权不变式到字段级溯源：每个创新点的设计、代码与踩坑")
_set(r, 10.2, False, GREY)

plain("这份文档按“创新点 → 设计 → 代码 → 边界”的顺序写。代码片段均取自 src/eag_guard，"
      "标注了文件名与函数名，可以直接对照仓库阅读。")

# ------------------------------------------------------------------ 0
h1("零、一页速览")

h2("0.1 四个核心创新点")
table(["#", "创新点", "一句话", "代码位置"],
      [["①", "授权范围作为不可变基准", "A=(T,O,P) 只从用户请求推导，任务期间不变",
        "scope.py: AuthorizationScope / ParamRule"],
       ["②", "证据切片与来源标记", "工具返回切成带出处的证据，字段与正文分存",
        "integrations/slicing.py"],
       ["③", "增量授权—证据—动作图", "六类节点、五类边，每轮只追加本轮节点",
        "eag.py: EAG.add_*"],
       ["④", "字段级溯源判定（FPR）", "从参数出发只沿支撑/派生回溯，看连到哪类根",
        "eag.py: EAG.fpr"]],
      widths=[1.0, 4.6, 6.4, 5.6])

h2("0.2 四个配套机制")
table(["#", "机制", "解决什么", "代码位置"],
      [["⑤", "归因器", "把“这个值从哪来”落到具体证据上", "provenance.py: Attributor"],
       ["⑥", "独立语义裁判", "结构判不了的两可情形，换一个看不见原文的裁判",
        "judge.py: JudgeView / LLMJudge"],
       ["⑦", "跨记录一致性", "收款人和金额必须来自同一条记录，防拼接", "pipeline.py: review"],
       ["⑧", "执行前核对 + 拒绝即反馈 + 输出审核", "防替换 / 让任务能继续 / 管住出口",
        "pipeline.py / audit.py"]],
      widths=[1.0, 4.6, 6.4, 5.6])

h2("0.3 模块依赖")
code(r"""
types.py          数据结构：Trust / Provenance / NodeKind / EdgeRel / Action / EvidenceItem
   │
scope.py          A=(T,O,P)：AuthorizationScope、ParamRule；规则解析器
   │
eag.py            图：Node/Edge、add_*、fpr()  ← 判定核心
   │
provenance.py     归因：normalize / value_in / Attributor
   │
judge.py          裁判：JudgeView、RuleJudge、LLMJudge
   │
audit.py          输出审核
   │
pipeline.py       Guard：prepare() / review() / run()
   │
integrations/agentdojo.py   EAGGuardElement（插在 ToolsExecutor 前）
""")

# ------------------------------------------------------------------ 1
h1("一、问题与不变的判定式")

h2("1.1 攻击面在哪")
plain("注入不是“模型被说服”这么抽象，它有固定路径：")
code(r"""
用户请求 ──→ 智能体 ──→ 调工具 ──→ 工具返回（攻击者可控的文字）
                                      │
                                      ▼
                              进入模型上下文
                                      │
                                      ▼
                        模型据此提议下一个动作（参数被污染）
""")
para([("关键观察：", True, NAVY, SONG),
      ("第一次调用工具之前，模型看到的所有内容都是可信的；从第一次工具返回开始，"
       "它的上下文就混入了不可信内容。", False, None, SONG)])
para([("所以判定不能问“模型为什么这么想”，只能问：", False, None, SONG),
      ("这次动作里的每一个值，有没有一个合法的来历。", True, NAVY, SONG)])

h2("1.2 不变式（写在 types.py 顶部的注释里）")
code(r"""
u            用户请求
A = (T, O, P) 授权范围：允许的工具 / 允许作用的对象 / 参数来源约束
s(v)         参数值来源：user-specified | user-delegated | injected

不变式：若存在 v 使 s(v)=injected，则动作不得执行（除非用户显式重新授权）。
动作 supported 当且仅当 tool∈T、object∈O、且每个参数值的 s(v) 属于前两类。
""")

h2("1.3 和 IPIGuard 的分界")
table(["", "IPIGuard", "EAG-Guard"],
      [["判定发生在", "计划期的图约束 + 执行期的工具准入", "每次动作执行前的值级判定"],
       ["判定对象", "工具名（在不在计划图里）", "每个参数值的来源 s(v)"],
       ["同工具换参数", "无对应机制（只有提示层偏置）", "FPR：值只连到不可信证据 → 拒"],
       ["状态", "计划图静态，执行期只读", "增量图，每轮追加"]],
      widths=[3.2, 7.2, 7.2])

# ------------------------------------------------------------------ 2
h1("二、创新点①：授权范围作为不可变基准")

h2("2.1 设计")
plain("解析器只看用户请求，产出三样东西：允许的工具 T、允许作用的对象 O、参数来源约束 P。"
      "它被冻结成一个不可变对象，任务期间不再变化。")

h2("2.2 数据结构（scope.py）")
code(r"""
@dataclass(frozen=True)
class AuthorizationScope:          # ← A = (T, O, P)
    tools:    frozenset[str]                        # T
    objects:  Mapping[str, frozenset[str]]          # O：类别 → 取值集合
    params:   Mapping[str, Mapping[str, ParamRule]] # P：工具 → 参数 → 规则
    request_text: str = ""
    read_only: bool = False
    notes: tuple[str, ...] = ()
""")
code(r"""
@dataclass(frozen=True)
class ParamRule:
    name: str
    allow: frozenset[Provenance] = {USER_SPECIFIED, USER_DELEGATED}
    delegable: bool = False
    delegation_source: str | None = None   # 例如 "file"
    mode: str = "field"                    # field | content
""")
para([("为什么用 frozenset 与 frozen=True：", True, RED, SONG),
      ("授权不变式要写在类型上——代码里想改直接报错，而不是靠“约定不改”。", False, None, SONG)])

h2("2.3 两种委托模式")
table(["模式", "取值允许来自", "典型场景", "代码判据"],
      [["field（字段型）", "被委托来源的结构化字段", "金额取账单的 Total、收款人取账单的 IBAN",
        "mode == \"field\""],
       ["content（内容型）", "被委托来源的正文", "把邮件正文转发、摘要网页内容",
        "mode == \"content\""]],
      widths=[3.4, 6.2, 5.4, 3.0])
plain("字段型是安全的关键：同一份账单，字段里的 98.70 能用，正文里的 9999 不能用。")

h2("2.4 解析的两条路径")
code(r"""
class ScopeParser(Protocol):
    def parse(self, request: str, tools: Sequence[ToolSpec]) -> AuthorizationScope: ...
""")
table(["实现", "怎么产出", "用途"],
      [["LLMScopeParser", "一次模型调用 → JSON → 六道代码校验", "主力"],
       ["RuleScopeParser", "正则 + 辞书，不调模型", "基线 / 兜底 / 证明 A 与模型无关"]],
      widths=[4.0, 7.6, 6.0])

h2("2.5 六道代码校验（parsing.py::_build）")
table(["步骤", "做什么", "为什么"],
      [["取 JSON", "从带 ``` 围栏或废话的输出里抠出第一个 JSON", "模型不保证只输出 JSON"],
       ["白名单", "工具名必须在清单里，否则丢弃并记 dropped", "防编造工具"],
       ["只读补全", "所有 read_only 工具默认进 T", "让模型逐个点名会漏，实测 UA 0.7→0.32"],
       ["动作词兜底", "请求含“付/删/发/改”时补对应工具进 T", "只补 T，不放松 O 与 P"],
       ["敏感参数强制字段型", "amount/recipient/iban/url 等一律 field", "这些字段决定钱给谁"],
       ["失败兜底", "解析异常 → 只读范围（fail-closed）", "宁可少做"]],
      widths=[3.4, 8.0, 6.2])

h2("2.6 踩过的坑（都写在注释里）")
bullet([("只读工具必须默认放行。", True, None, SONG),
        ("若让模型逐个点名，它换个检索路径（search_emails → get_unread_emails）就会被判“不在 T”，"
         "实测把 25 对切片的 UA 从 0.7 压到 0.32。", False, None, SONG)])
bullet([("不能把 update_user_info / update_password 补进 T。", True, None, SONG),
        ("banking 的注入目标正是改密码/改用户信息，补进去等于开门，实测 ASR 4%→11%。", False, None, SONG)])
bullet([("action verb 词典要覆盖真实措辞。", True, None, SONG),
        ("缺 adjust/rent/payment 时 update_scheduled_transaction 进不了 T，三个守卫样本里被拒 12 次。", False, None, SONG)])

# ------------------------------------------------------------------ 3
h1("三、创新点②：证据切片与来源标记")

h2("3.1 数据结构（types.py）")
code(r"""
@dataclass(frozen=True)
class EvidenceItem:
    id: str
    source: str            # "inbox:msg-42"、"file:bill.pdf"、"web:https://..."
    trust: Trust           # TRUSTED / UNTRUSTED（只有用户请求与系统提示可信）
    text: str
    fields: Mapping[str, str] = {}   # 结构化字段：{"amount": "98.70", "iban": "UK12…"}
    authorized: bool = False         # 是否来自“用户点名要读的资源”
    producer: str = ""               # 产生它的工具名，用于识别清单类读取
    resource: str | None = None      # 工具实际请求的资源（不是正文里的值）
""")

h2("3.2 为什么必须切片")
plain("工具返回是一大段文本。如果不切：")
table(["不切片的后果", "具体"],
      [["字段与正文混在一起", "只能做字符串匹配，“正文里写个数就能冒充金额”"],
       ["无法区分“用户点名的材料”和“顺手读到的内容”", "摘要/转发会被误判为注入"],
       ["无法追溯“这个值来自哪条记录”", "拼接攻击（收款人来自 A、金额来自 B）识别不了"]],
      widths=[7.0, 10.6])

h2("3.3 切片规则（integrations/slicing.py）")
plain("按工具类型定制：交易流水一笔一条；账单整份一条并抽 total/iban；邮件一封一条并抽 from/subject；"
      "清单类读取（get_channels 等）返回的是“环境里有哪些对象”，标记 usable 供候选集合使用。")

h2("3.4 在流程里的位置")
code(r"""
# integrations/agentdojo.py  （工具执行后）
slices = slice_evidence(call.function, text)
for item in slices:
    if f"e:{item.id}" not in self.state.graph:
        self.state.graph.add_evidence(item)   # ← 入图（挂载点③）
""")

# ------------------------------------------------------------------ 4
h1("四、创新点③：增量授权—证据—动作图")

h2("4.1 节点与边（types.py 的枚举）")
code(r"""
class NodeKind(str, Enum):
    USER_REQUEST = "user_request"
    AUTHORIZATION = "authorization"
    DELEGATION   = "delegation"
    TOOL         = "tool"
    OBJECT       = "object"
    EVIDENCE     = "evidence"
    ACTION       = "action"
    PARAM        = "param"

class EdgeRel(str, Enum):
    SUPPORTS = "supports"    # 授权/证据 → 参数：该值由此支撑
    DERIVES  = "derives"     # 委托 → 参数：该值由委托查找派生
    PRODUCES = "produces"    # 动作 → 证据：动作产生的新证据
    GRANTS   = "grants"      # 用户请求 → 授权
    DELEGATES= "delegates"   # 用户请求 → 委托
""")

h2("4.2 建图：一个任务只做一次的部分（Guard.prepare）")
code(r"""
graph = EAG()
user_node = graph.add_user_request(request)          # u:request

for tool in sorted(scope.tools):                     # T → 工具节点 + 授权节点
    tool_node = graph.add_tool(tool)
    auth = graph.add_authorization(f"工具 {tool}", {"tool": tool})
    graph.add_edge(auth.id, tool_node.id, EdgeRel.SUPPORTS)

for klass, values in sorted(scope.objects.items()):  # O → 对象节点 + 授权节点
    for value in sorted(values):
        object_node = graph.add_object(klass, str(value))
        auth = graph.add_authorization(f"{klass}={value}", {"object": value})
        graph.add_edge(auth.id, object_node.id, EdgeRel.SUPPORTS)

delegation_nodes = {}
for rule in scope.delegations():                     # P 中的委托 → 委托节点
    node = graph.add_delegation(rule.name, rule.delegation_source or "", user_node.id)
    delegation_nodes.setdefault(rule.name, node.id)
""")

h2("4.3 增量：每轮只加本轮的东西（Guard.review）")
code(r"""
state.graph.add_action(action)               # 动作节点 act:<id>

attributions = self.attributor.attribute(action, spec, state.scope, ctx)
for attr in attributions:                    # 每个参数一个节点 + 它的根边
    state.graph.add_param(action.id, attr.attribution, attr.roots)
""")
code(r"""
def add_param(self, action_id, attribution, roots):
    node = self.add_node(Node(self._next_id("p"), NodeKind.PARAM,
                              f"{attribution.param}={attribution.value!r}"))
    self.add_edge(f"act:{action_id}", node.id, EdgeRel.SUPPORTS)   # 动作挂出实参
    for root_id, rel in roots:                                     # 根 → 参数
        if root_id in self._nodes:
            self.add_edge(root_id, node.id, EdgeRel(rel))
    return node
""")
para([("增量体现在三处：", True, NAVY, SONG),
      ("① 每轮只新增动作/参数/证据节点；② 旧节点不删除也不重判；③ 判定只针对本轮新参数。"
       "但回溯仍可走到很早以前的委托节点——图一直攒着，回溯临时走。", False, None, SONG)])

h2("4.4 导出")
plain("EAG.to_dict() 把 nodes/edges 全量导出，写进逐对结果 JSON，便于复查。")

# ------------------------------------------------------------------ 5
h1("五、创新点④：字段级溯源判定 FPR")

h2("5.1 代码全文（eag.py::EAG.fpr）")
code(r"""
def fpr(self, param_node_id: str) -> FPRResult:
    node = self._nodes[param_node_id]
    trusted, untrusted = [], []
    seen = {param_node_id}
    stack = [param_node_id]
    while stack:
        current = stack.pop()
        for edge in self._in.get(current, []):          # 只看入边（反向）
            if edge.rel not in (EdgeRel.SUPPORTS, EdgeRel.DERIVES):
                continue                                 # ← 只走两类边
            src = self._nodes.get(edge.src)
            if src is None or src.id in seen:
                continue
            seen.add(src.id)
            if src.kind is NodeKind.EVIDENCE:
                if src.trust is Trust.UNTRUSTED:
                    untrusted.append(src.id)             # 不可信根
                else:
                    trusted.append(src.id)
            elif src.kind in (NodeKind.AUTHORIZATION, NodeKind.DELEGATION,
                              NodeKind.USER_REQUEST):
                trusted.append(src.id)                   # 可信根
            else:
                stack.append(src.id)                     # 继续往上
    allow = bool(trusted)                                # ← 存在性判定
    return FPRResult(..., trusted_roots=tuple(trusted),
                     untrusted_roots=tuple(untrusted), allow=allow)
""")

h2("5.2 逐行解释")
table(["代码", "含义"],
      [["stack / seen", "显式栈做 DFS，seen 防环（产出边若混进来会成环，这里也兜底）"],
       ["edge.rel not in (SUPPORTS, DERIVES)", "只承认“值的来历”这两类边"],
       ["src.kind is EVIDENCE and untrusted", "不可信根：记下来，不放行"],
       ["src.kind in (AUTHORIZATION, DELEGATION, USER_REQUEST)", "可信根：记下来，放行"],
       ["else: stack.append", "工具/对象等中间节点继续往上走"],
       ["allow = bool(trusted)", "存在性：有一个可信根就过"]],
      widths=[8.4, 9.2])

h2("5.3 为什么只走两类边")
table(["边", "它回答的问题", "若参与回溯"],
      [["SUPPORTS / DERIVES", "这个值的来历", "✓ 正是要问的"],
       ["GRANTS", "谁允许做这件事", "会把“用户提过转账”读成“这个金额是用户给的”"],
       ["DELEGATES", "这条委托谁定的", "跳级：把“委托取得”标成“用户直接指定”"],
       ["PRODUCES", "这个证据哪来的", "参数→动作→证据→参数 成环，动作自证"]],
      widths=[4.2, 6.4, 7.0])

h2("5.4 三分类折算（provenance_from_fpr）")
code(r"""
def provenance_from_fpr(result):
    if result.allow:            return Provenance.USER_SPECIFIED
    if result.untrusted_roots:  return Provenance.INJECTED
    return Provenance.UNATTRIBUTED
""")

h2("5.5 复杂度")
plain("每个参数一次 DFS，V、E 是本图节点与边；单步判定 O(V+E)。因为图是增量累积的，"
      "V 随轮数增长，但单轮新增的边很少，实际开销与轮数线性。")

# ------------------------------------------------------------------ 6
h1("六、配套⑤：归因器——把值落到来源")

h2("6.1 归一化：先让“看起来一样”的变一样")
code(r"""
def normalize(value):
    text = unicodedata.normalize("NFKC", str(value))   # 全角→半角
    text = text.casefold()
    text = text.translate(_CURRENCY)                   # 去掉 , $ € ¥ 空格
    return _WS.sub(" ", text).strip()
""")
plain("再叠三种等价展开：日期（2024-05-26 ↔ May 26th）、URL（带不带协议/www）、数值（10 ↔ 10.0 ↔ 10.00）。"
      "长值（>60 字符）改用 40 字窗口滑窗匹配，应对“模型把原文包进自己的句子里”。")

h2("6.2 四个分支（Attributor.attribute）")
code(r"""
for param, raw in action.args.items():
    value = str(raw) if raw is not None else ""
    rule = scope.rule(action.tool, param)

    # 1) 用户直接给出
    if value_in(request_norm, value):
        → USER_SPECIFIED，根 = (user_node, "supports")

    # 2) 用户委托：字段型只认结构化字段
    if rule.allows_delegation:
        pool = ctx.from_source(rule.delegation_source)
        if rule.content_delegation:
            hits = [e for e in pool if value_in(normalize(e.text), value)]
        else:
            hits = [e for e in pool
                    if e.fields.get(param) is not None
                    and _same_value(e.fields[param], value)]
        if hits: → USER_DELEGATED，根 = (委托节点, "derives")

    # 3) 只出现在不可信内容中
    hits = [e for e in ctx.untrusted() if value_in(normalize(e.text), value)]
    if hits:
        if not field_mode and any(e.authorized for e in hits):
            → USER_DELEGATED（用户点名的材料）
        else:
            → INJECTED，根 = [(e:<id>, "supports")]

    # 4) 都不是
    → UNATTRIBUTED，无根
""")

h2("6.3 三个关键设计")
bullet([("字段型不退回文本匹配。", True, None, SONG),
        ("注释里写着“兜底：来源本身不可被攻击者写入就退化成整文匹配——已删除”，"
         "因为 banking 的注入会把账单 Total/IBAN 整行替换，兜底会把攻击者写的账户认成委托来的收款人。", False, None, SONG)])
bullet([("不认“sender 别名”。", True, None, SONG),
        ("试过让收款人也能来自交易的 sender 字段以支持“退钱给他”，实测 ASR 0.69%→2.78%、效用不变，回退。", False, None, SONG)])
bullet([("来源别名归一。", True, None, SONG),
        ("解析器说 webpage/email，证据标签是 web/inbox；不归一化委托会静默落空（“总结网页发到频道”就是被这个坑挡掉的）。", False, None, SONG)])

# ------------------------------------------------------------------ 7
h1("七、配套⑥：独立语义裁判")

h2("7.1 它看到什么（judge.py::JudgeView.render）")
code(r"""
【用户请求】
把 10 月房租付了，房东 UK12345678901234567890，金额按账单 bill.pdf 的合计
【授权范围】
允许的工具：read_file, send_money
允许的 recipient：UK12345678901234567890
参数 send_money.amount：允许由 file 运行时取值
【候选动作】
send_money(recipient='UK12345678901234567890', amount=9999, ...)
【代码已核对，无需你再判断】
工具 send_money：在授权范围内
作用对象：在授权范围内
【参数结构化记录】
- recipient = 'UK1234…' → 用户请求中直接给出
- amount = 9999 → 只出现在不可信内容中，且未被委托；取自账单文件的返回
""")

h2("7.2 它看不到什么")
table(["刻意不给", "原因（代码注释原话）"],
      [["Action.intent（规划器自述意图）", "“绝不进裁判上下文”——它是在读过注入内容之后编的"],
       ["工具返回原文", "“原文是被污染的东西，看了就会被带偏”"],
       ["对话上下文", "同上"]],
      widths=[6.4, 11.2])

h2("7.3 两种实现")
table(["实现", "做什么", "用途"],
      [["RuleJudge", "按授权范围逐项核对，确定性", "纯结构消融臂"],
       ["LLMJudge", "结构化视图 + 四问 + JSON 输出", "主实验"]],
      widths=[3.6, 8.6, 5.4])

h2("7.4 两个省成本/防误杀的细节")
bullet([("只读动作不进裁判：", True, None, SONG),
        ("读操作没有副作用，对象白名单已经挡住越界读取；每次读都问一遍模型既贵又容易误杀。", False, None, SONG)])
bullet([("豁免参数 + 方向性参数：", True, None, SONG),
        ("untargeted 下只把收件人/收款人/金额/链接/作用对象交给裁判；正文类（body/subject/location）豁免——"
         "它们改不了数据流向，却几乎不可能逐字出现在用户请求里。", False, None, SONG)])
bullet([("候选集合：", True, None, SONG),
        ("清单类读取返回的可选项一起给裁判，它才能“按用户规则算应选哪个”，而不是凭感觉否决。", False, None, SONG)])

# ------------------------------------------------------------------ 8
h1("八、配套⑦：跨记录一致性（防拼接）")

code(r"""
money_group = {"recipient", "payee", "amount", "total"}
delegated_money = [a for a in attributions
                   if a.param in money_group
                   and a.provenance is Provenance.USER_DELEGATED
                   and a.attribution.evidence_ids]
if len(delegated_money) >= 2:
    common = set(delegated_money[0].attribution.evidence_ids)
    for item in delegated_money[1:]:
        common &= set(item.attribution.evidence_ids)
    if not common:
        reasons.append("收款人与金额来自不同的记录（可能是拼接出来的付款），拒绝")
""")
para([("为什么需要它：", True, NAVY, SONG),
      ("注入常把伪造的 IBAN 塞在另一处（另一条消息、另一段正文），这样“收款人来自 A、金额来自 B”"
       "的付款就是拼出来的——单看每个值都有出处，合起来却是假的。", False, None, SONG)])

# ------------------------------------------------------------------ 9
h1("九、配套⑧：执行前核对、拒绝即反馈、输出审核")

h2("9.1 签名核对（pipeline.py::review 末尾）")
code(r"""
if action.signature() != self._signature(record):
    record.decisions.append(Decision("precheck", False, ("动作在审核后被修改",)))
""")
code(r"""
# types.py
def signature(self) -> str:
    parts = [f"{k}={self.args[k]!r}" for k in sorted(self.args)]
    return f"{self.tool}({', '.join(parts)})"
""")

h2("9.2 拒绝即反馈（pipeline.py::_deny）")
code(r"""
def _deny(self, planner, action, record):
    if self.config.feedback == "weak":
        planner.reject(action, ("动作被拒绝",))          # 消融臂：不给原因
    else:
        planner.reject(action, record.reasons)          # 主配置：给可操作原因
""")
plain("主配置的理由长这样：“参数 amount=9999 只可溯源到不可信内容（FPR 无可信根路径）”。"
      "规划器据此改成 98.70 重提，这是“拒绝不是终点”的实现。")

h2("9.3 输出审核（audit.py::OutputAudit.audit）")
code(r"""
# 规则一：带注入标记的外部内容，答复里逐字重合的片段一律抹掉
poisoned = [e for e in evidence
            if e.trust is Trust.UNTRUSTED and _POISON.search(e.text or "")]
for item in poisoned:
    for block in self._leaked_blocks(out, item.text):
        out = out.replace(block, "〔已移除外部内容〕")

# 规则二：既像指令、又确实出自不可信内容的句子，抹掉
for item in evidence:
    if item.trust is not Trust.UNTRUSTED: continue
    for sentence in re.split(r"(?<=[。！？.!?])\s*", out):
        if len(sentence) < self.min_block or sentence not in item.text: continue
        if any(p.search(sentence) for p in _INSTRUCTION_PATTERNS):
            out = out.replace(sentence, "〔已移除外部内容〕")
""")
para([("两条规则的来历（注释里写着）：", True, RED, SONG),
      ("旧口径“对所有未授权证据比对”会把合法答案也抹掉（travel UA 0.55→0.25），"
       "所以收窄成“既像指令、又有出处”两个条件同时成立。", False, None, SONG)])

# ------------------------------------------------------------------ 10
h1("十、全流程代码走读")

h2("10.1 Guard.run：一个任务的骨架")
code(r"""
def run(self, request, env, case_id="case"):
    state = self.prepare(request)                       # ① 解析 + 建图根节点
    trace = Trace(case_id=case_id, request=request, scope=state.scope,
                  graph=state.graph, config=self.config)
    planner = self.planner_factory(request, state.scope)
    evidence = []

    for step in range(self.config.max_steps):
        action = planner.propose(step)                  # 模型提议动作
        if action is None: break
        record = self.review(state, action, evidence, step)   # ② 判定
        trace.steps.append(record)

        if not all(d.allowed for d in record.decisions):
            self._deny(planner, action, record)         # 拒绝 + 给原因
            continue

        execution = env.execute(action)                 # ③ 真正执行
        record.executed = True
        for item in execution.evidence:
            if f"e:{item.id}" not in state.graph:
                state.graph.add_evidence(item)          # 入图
            evidence.append(item)
        planner.observe(action, execution.result)

    trace.final_answer = planner.finalize()
    trace.audit = self.audit.audit(trace.final_answer, evidence)   # ④ 出口审核
    trace.final_answer = trace.audit.text
    return trace
""")

h2("10.2 Guard.review：三步判定")
code(r"""
spec = self.tools.get(action.tool)
state.graph.add_action(action)
attributions = self.attributor.attribute(action, spec, state.scope, ctx)

# 1) 结构判定：T / O / 参数来源
if self.config.enable_fpr:
    decision = self._fpr_decision(action, attributions, spec, state.scope)
    if not decision: return record

# 2) 独立语义裁判（只读动作可跳过）
if self.config.enable_judge and not (read_only and not touches_url):
    view = JudgeView(...)
    decision = self.judge.review(view)
    if not decision: return record

# 3) 执行前签名核对
if action.signature() != self._signature(record):
    record.decisions.append(Decision("precheck", False, ("动作在审核后被修改",)))
""")

h2("10.3 _fpr_decision：结构判定的五类理由")
table(["检查", "触发条件", "理由文本"],
      [["工具未注册", "spec is None", "工具 X 未注册"],
       ["工具不在 T", "not scope.tool_allowed", "工具 X 不在授权范围 T 内"],
       ["对象是仿冒域名", "scope.is_lookalike_object", "对象 'x' 是授权域名的仿冒"],
       ["对象不在 O", "not object_allowed 且字面不在请求里", "对象 'x' 不在授权范围 O 内"],
       ["参数来源不合格", "rule.permits(s(v)) 为假", "参数 p=v 只可溯源到不可信内容 / 无法归因"],
       ["URL 只来自注入", "param in URL_PARAMS 且 provenance=INJECTED", "链接 'x' 只出现在不可信内容中"],
       ["跨记录不一致", "收款人与金额无公共证据", "收款人与金额来自不同的记录"]],
      widths=[4.0, 6.6, 7.0])

h2("10.4 在 AgentDojo 里怎么接（EAGGuardElement.query）")
code(r"""
if self.state is None:
    self.state = self.guard.prepare(query)          # ① 只解析一次

for call in calls:                                  # 模型可能一次提多个调用
    action = Action(id=call.id, tool=call.function, args=call.args)
    record = self.guard.review(self.state, action, self.evidence, self._step)
    if all(d.allowed for d in record.decisions):
        allowed.append(call)
        if 全部参数都是 USER_SPECIFIED/USER_DELEGATED:
            self._sanctioned.add(call.id)           # 标记“这是用户委托的读取”
    else:
        denied.append((call, record))
        for item in record.attributions:
            if item.provenance is Provenance.INJECTED:
                self.blocked_values.add(item.value)
""")
para([("两个必须做对的细节：", True, RED, SONG)], space_before=2)
bullet([("被拒的调用必须从 assistant 消息里摘掉。", True, None, SONG),
        ("AgentDojo 的栈回溯会把消息里所有 tool_call 都算成“调用过”，哪怕没执行——留着它，"
         "官方 security 判定会误记为“攻击成功”。", False, None, SONG)])
bullet([("放行与“参数都在授权内”必须写在同一个分支。", True, None, SONG),
        ("踩过的坑：写成两个独立判断，导致同一个调用既执行又记进 denied，模型收到“动作被拒绝”，"
         "回答“我没有权限查看日历”，而工具明明返回了数据。", False, None, SONG)])

# ------------------------------------------------------------------ 11
h1("十一、消融：一份配置打六个臂")

code(r"""
@dataclass
class GuardConfig:
    name: str = "eag"
    enable_fpr: bool = True          # 字段级溯源
    enable_judge: bool = True        # 独立语义裁判
    allow_delegation: bool = True    # 是否承认委托边
    read_only_policy: bool = False   # 只读策略
    read_policy: str = "allow_all"   # audit_all | no_target | allow_all
    strict_params: tuple[str, ...] = ()       # 资金流向字段，untargeted 下也不放宽
    field_strict_params: tuple[str, ...] = () # 只认结构化字段
    delegation: str = "untargeted"   # untargeted | targeted
    structure_only: bool = False     # 纯结构（只允许用户直接指定）
    output_audit: bool = True
    feedback: str = "strong"         # strong | weak
    max_steps: int = 8
""")
table(["消融臂", "配置", "验证什么"],
      [["无防御", "不装守卫", "ASR 基线"],
       ["纯结构", "structure_only=True, enable_fpr=True", "只有白名单能挡多少"],
       ["结构 + 委托", "structure_only=False, enable_judge=False", "委托本身贡献多少"],
       ["EAG（完整）", "enable_fpr + enable_judge", "核心"],
       ["- 裁判", "enable_judge=False", "裁判的边际贡献"],
       ["- FPR", "enable_fpr=False", "溯源的边际贡献"]],
      widths=[3.6, 7.8, 6.2])

# ------------------------------------------------------------------ 12
h1("十二、开销")

table(["环节", "每次任务", "每次动作"],
      [["解析", "1 次模型调用", "—"],
       ["归因", "—", "O(参数数 × 证据数) 文本匹配"],
       ["FPR", "—", "O(V+E) 图遍历"],
       ["裁判", "—", "1 次模型调用（只读动作可跳过）"],
       ["输出审核", "1 次", "—"]],
      widths=[4.0, 6.0, 7.6])
plain("实测口径：629 对全量，ASR 0.64%、UA 0.7122（报告口径）；换 qwen3.5-27b 后 ASR 0.79%、UA 0.7154。"
      "口径差异与模型不同有关，绝对值不可跨模型比较。")

# ------------------------------------------------------------------ 附录
h1("附录 A　代码索引")
table(["文件", "关键符号", "作用"],
      [["types.py", "Trust / Provenance / NodeKind / EdgeRel / Action / EvidenceItem / Decision", "数据模型"],
       ["scope.py", "AuthorizationScope / ParamRule / RuleScopeParser", "A 的结构与规则解析"],
       ["parsing.py", "LLMScopeParser / describe_tools / tools_implied_by_request", "模型解析 + 校验"],
       ["eag.py", "EAG.add_* / EAG.fpr / provenance_from_fpr", "建图与溯源"],
       ["provenance.py", "normalize / value_in / Attributor", "归因"],
       ["judge.py", "JudgeView / RuleJudge / LLMJudge", "裁判"],
       ["audit.py", "OutputAudit / AuditResult", "出口审核"],
       ["pipeline.py", "Guard.prepare / review / run / _fpr_decision / _deny", "主流程"],
       ["integrations/agentdojo.py", "EAGGuardElement / OutputAuditElement", "接入"],
       ["integrations/slicing.py", "slice_evidence", "证据切片"]],
      widths=[4.6, 8.0, 5.0])

doc.add_paragraph()
para([("一句话：", True, NAVY, SONG),
      ("这套东西的创新不在“又加了一个检查”，而在把判定对象从工具名下沉到参数值，"
       "并且用一个只承认两类边的图，把“这个值有没有合法来历”变成可计算、可解释、可复现的判定。",
       False, None, SONG)], space_after=2)

out = os.path.join(HERE, "EAG-Guard-创新点与代码实现.docx")
doc.save(out)
print("saved:", out, os.path.getsize(out), "bytes")
