# -*- coding: utf-8 -*-
"""《工具清单与提示词的来历》逐节精讲与答疑。"""
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

doc = Document()
normal = doc.styles["Normal"]
normal.font.name = SONG
normal.font.size = Pt(12)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), SONG)
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(6)

for sec in doc.sections:
    sec.top_margin = Cm(2.4)
    sec.bottom_margin = Cm(2.4)
    sec.left_margin = Cm(2.7)
    sec.right_margin = Cm(2.7)


def _set(run, size, bold=False, font=SONG):
    run.font.size = Pt(size)
    run.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)
    run.font.name = "Consolas" if font == MONO else "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font if font != MONO else "宋体")


def para(text, indent=True, size=12, bold=False, font=SONG,
         space_before=0, space_after=6, align=None):
    par = doc.add_paragraph()
    fmt = par.paragraph_format
    fmt.line_spacing = 1.5
    fmt.space_before = Pt(space_before)
    fmt.space_after = Pt(space_after)
    if indent:
        fmt.first_line_indent = Pt(size * 2)
    if align is not None:
        par.alignment = align
    run = par.add_run(text)
    _set(run, size, bold, font)
    return par


def title(text, size=15):
    return para(text, indent=False, size=size, bold=True, font=HEI,
                align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)


def sub(text, size=12):
    return para(text, indent=False, size=size,
                align=WD_ALIGN_PARAGRAPH.CENTER, space_after=14)


def heading(text, size=14):
    return para(text, indent=False, size=size, bold=True, font=HEI,
                space_before=15, space_after=6)


def step(text, size=12):
    return para(text, indent=False, size=size, bold=True, font=HEI,
                space_before=10, space_after=3)


def code(text, size=9.5):
    for ln in text.strip("\n").split("\n"):
        par = doc.add_paragraph()
        fmt = par.paragraph_format
        fmt.left_indent = Cm(0.8)
        fmt.space_before = Pt(0)
        fmt.space_after = Pt(0)
        fmt.line_spacing = 1.15
        run = par.add_run(ln if ln else " ")
        _set(run, size, False, MONO)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def table(headers, rows, widths, size=10.5):
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
        _set(r, size, True, HEI)
    trPr = t.rows[0]._tr.get_or_add_trPr()
    trPr.append(trPr.makeelement(qn("w:tblHeader"), {}))
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            _set(r, size, False, SONG)
    for row in t.rows:
        trPr = row._tr.get_or_add_trPr()
        trPr.append(trPr.makeelement(qn("w:cantSplit"), {}))
    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w)
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def qa(q, a):
    p = para(q, indent=False, size=12, bold=True, font=HEI, space_before=8, space_after=2)
    para(a, space_after=4)


# ==================================================================
title("《工具清单与提示词的来历》逐节精讲与答疑")
sub("—— 每句话、每段代码、以及导师可能追问的地方")

para("这份材料是对那份文档的“讲稿版”：先把七节逐节拆开讲清楚，再把五段代码逐行解释，"
     "最后列出导师最可能追问的问题和准备好的回答。")

# ------------------------------------------------------------------ 一
heading("一、一页读懂：这份文档在回答什么")

para("它只追踪一件事：模型面前那几行工具清单，是怎么来的；模型又是怎么用它挑出工具。")

para("整条链路四个环节，只有第三个涉及模型：")

table(["环节", "谁在做", "产物"],
      [["① 读取", "代码：toolspecs_from_suite", "ToolSpec（补上只读、对象参数）"],
       ["② 渲染", "代码：describe_tools", "四行自然语言文字"],
       ["③ 挑选", "模型：续写 JSON", "tools / objects / delegations"],
       ["④ 校正", "代码：四道校验", "授权范围 A=(T,O,P)"]],
      widths=[2.6, 6.4, 7.4])

para("换句话说：清单是代码从环境里“翻译”出来的，模型只是照着它挑。")

# ------------------------------------------------------------------ 二
heading("二、逐节精讲")

step("第一节　环境里的工具定义")
para("原文说“工具是测试环境里注册的函数，每个工具有名字、参数、一句说明”。这句话在强调："
     "清单的原料不是我们编的，是环境给的。")
para("那张 7 行的表，实际是把银行域 11 个工具压成了 7 类。看几个代表：")
table(["工具", "参数说明", "为什么重要"],
      [["send_money", "recipient, amount, subject, date", "攻击的主要目标——改金额、改收款人"],
       ["read_file", "file_path", "读账单的入口，注入就是从这里进来的"],
       ["update_password", "password", "最敏感的写操作，banking 注入常打它"],
       ["get_* 系列", "无参数", "纯查询，只读，不会改状态"]],
      widths=[4.2, 6.4, 6.0])
para("这一节的潜台词是：清单里的每个工具都是真能改变环境状态的函数，不是演示用的假动作。")

step("第二节　把环境定义读成内部结构")
para("环境给的是函数，我们程序里要的是结构化数据，所以要转换一次。八行代码逐行看：")
table(["代码", "做了什么", "为什么必须有"],
      [["for fn in suite.tools", "遍历环境里的每个工具", "工具集合由环境决定，不是写死的"],
       ["schema = fn.parameters.model_json_schema()", "取出参数的 JSON Schema", "这是获取参数名与类型的标准方式"],
       ["props = tuple(schema.get(\"properties\", {}))", "把参数名按顺序取出", "后面要原样展示给模型"],
       ["mapping.get(fn.name, (None, \"object\"))", "查人工表，找不到就返回默认值", "保证不崩：查不到就给空对象"],
       ["ToolSpec(name=…, params=…)", "组装内部结构", "后续所有代码只认这个结构"],
       ["read_only=_is_read_only(fn.name)", "按名字前缀判只读", "签名里没有“是否只读”这个信息"]],
      widths=[6.6, 5.4, 4.6])
para("这一节最关键的一句话是表格最后一列：name 和 params 是环境给的，read_only、object_param、"
     "object_class 是我们补的。为什么要补？因为函数签名只说“有个参数叫 recipient”，"
     "不会说“这个参数决定钱给谁”。")

step("第三节　渲染成模型看得懂的清单")
para("内部结构是给程序看的，模型要看文字。八行代码做的事就是“拼字符串”：")
code('''
def describe_tools(tools):
    lines = []
    for spec in tools:
        params = ", ".join(spec.params) or "无"          # 参数拼成 a, b, c
        klass = f"，对象类别={spec.object_class}" if spec.object_param else ""
        kind = "只读" if spec.read_only else "有副作用"
        lines.append(f"- {spec.name}（{kind}）：参数 [{params}]{klass}")
    return "\\n".join(lines)
''')
para("逐行解释：")
table(["行", "含义"],
      [["params = …", "把参数列表拼成“recipient, amount, subject”；没有参数就写“无”"],
       ["klass = …", "只有当工具有作用对象时，才追加“，对象类别=xxx”"],
       ["kind = …", "只读工具标“只读”，其余标“有副作用”"],
       ["lines.append(…)", "拼成一行：- 名字（性质）：参数 [...]，对象类别=..."],
       ["return \"\\n\".join", "每行一条，用换行连起来"]],
      widths=[5.6, 11.0])
para("这一节还交代了一件事：清单里没有英文说明。原文写“注意它只包含名字和参数”——"
     "这是个取舍，也是后面要准备的追问点。")

step("第四节　把清单拼进提示词")
para("清单只是素材，模型不知道拿它干什么，所以要配一段“说明书”。两段的分工：")
table(["部分", "内容", "作用"],
      [["系统提示", "你是任务解析器 + T/O/P 定义 + 输出格式 + 七条规则", "告诉模型“你是谁、要填什么表、按什么规矩填”"],
       ["用户消息", "工具清单 + 用户请求", "告诉模型“有哪些工具、用户说了什么”"]],
      widths=[3.0, 7.6, 6.0])
para("注意系统提示的第一句：“你看不到任何工具返回内容。”这句不是客套——它是在给模型划边界，"
     "防止它去猜账单里写了什么。")

step("第五节　提示词是怎么来的")
para("这一节是全文最有分量的：七条规则，每一条都对应一次实测失败。挑三条说：")
table(["规则", "背后的坑"],
      [["2. 用户没点名就不要写对象", "曾经要求模型“把点名的值都写进去”，结果 slack 的 ASR 从 9.52% 涨到 11.43%、"
                          "UA 从 0.40 掉到 0.39——两头都变差，回退了"],
       ["1. 必需的工具要列全", "模型漏列前置步骤（该读账单却没列 read_file），任务直接做不完"],
       ["7. 写进字段时用 content 委托", "“把酒店地址写进日历”这类任务，地址是从读取来的，不写委托就被判成注入"]],
      widths=[5.4, 11.2])
para("还有两处不是提示词、而是代码兜底：只读工具默认放行、动作词补全。这两条的来历也写着——"
     "前者因为模型换个检索路径就被误判（UA 0.7→0.32），后者因为漏了 adjust/rent 这几个词，"
     "工具进不了 T、被拒 12 次。")

step("第六节　模型怎么从这句话里挑出工具")
para("这一节回答“模型凭什么”。三条线索：工具名是人话、参数名有含义、任务结构有常识。")
para("最后一句最关键：“它不是在检索，而是在续写。”——模型不是去清单里做匹配查询，"
     "而是在生成 JSON 时，把概率最高的工具名一个 token 一个 token 写出来。")

step("第七节　整条链路再看一遍")
para("那张流程图的价值是把“谁负责什么”钉死：四个箭头里，只有“模型”那一格是它干的，"
     "读、渲染、校正都是代码。这也是“换模型不改 T/O/P 形态”的原因。")

# ------------------------------------------------------------------ 三
heading("三、五段代码逐段精读")
para("把文档里出现过的代码汇总，逐行注释。")

step("代码一：读取工具（toolspecs_from_suite 的核心四行）")
code('''
for fn in suite.tools:                                   # 环境的工具集合
    schema = fn.parameters.model_json_schema()           # 参数的结构描述
    props = tuple(schema.get("properties", {}))          # 参数名，按声明顺序
    object_param, object_class = mapping.get(fn.name, (None, "object"))
    specs[fn.name] = ToolSpec(                           # 组装成内部结构
        name=fn.name, params=props,
        object_param=object_param, object_class=object_class,
        read_only=_is_read_only(fn.name),
    )
''')
para("两个细节值得讲：")
para("第一，mapping.get 的第二个参数是默认值 (None, \"object\")——查不到映射时不会报错，"
     "但这个工具也就没有对象检查了。这是“安全默认”与“可用默认”之间的取舍。")
para("第二，read_only 是推断出来的，不是读出来的。这是全文唯一一处“猜”的地方。")

step("代码二：渲染清单（describe_tools）")
code('''
params = ", ".join(spec.params) or "无"     # 空参数写“无”，避免出现“参数 []”
kind = "只读" if spec.read_only else "有副作用"   # 两个字概括工具性质
klass = f"，对象类别={spec.object_class}" if spec.object_param else ""
lines.append(f"- {spec.name}（{kind}）：参数 [{params}]{klass}")
''')
para("为什么要写“对象类别”这四个字？因为模型要据此填 objects 的键。没有这个提示，"
     "它可能把对象类别写成“收款人”这种中文，代码就对不上了。")

step("代码三：只读判定（_is_read_only）")
code('''
READ_ONLY_PREFIXES = ("get_", "read_", "list_", "search_", "check_", "view_", "fetch_")
def _is_read_only(name):
    return name.startswith(READ_ONLY_PREFIXES)
''')
para("一行判断，覆盖 AgentDojo 里的绝大多数查询工具。风险是“名字骗人”——一个会写数据的工具如果叫 get_xxx，"
     "就会被误判成只读。这是已知局限，靠代码审查兜。")

step("代码四：对象参数映射（DEFAULT_OBJECT_PARAMS 节选）")
code('''
"send_money": ("recipient", "recipient"),     # 收款人是作用对象，类别叫 recipient
"read_file":  ("file_path", "file"),          # 文件路径是作用对象，类别叫 file
"send_email": ("recipients", "recipient"),    # 收件人是作用对象
''')
para("这张表是纯人工的，它决定了“O 检查哪个参数”。漏一条，那个工具就只剩工具名检查。")

step("代码五：动作词表（VERB_TOOLS 节选）")
code('''
(("pay", "transfer", "refund", "付款", "转账", "退款"), ("send_money",)),
(("update", "change", "adjust", "修改", "调整"),       ("update_scheduled_transaction",)),
''')
para("它是“模型漏列”的补丁：请求里出现左边的词，就把右边工具补进 T。只补 T，不动 O 和 P。")

# ------------------------------------------------------------------ 四
heading("四、导师可能问的问题与回答")

step("A. 关于定义来源")
qa("问：这个工具清单是你们自己写的吗？",
   "答：不是。工具名和参数来自 AgentDojo 环境的函数签名，是运行时读出来的；我们只人工补了两样签名里没有的信息——"
   "哪个参数是作用对象、以及这个名字算不算只读。所以清单是“环境的事实 + 两张小表”。")
qa("问：为什么银行域只有 11 个工具？",
   "答：这是 AgentDojo 为银行域定义的全部工具。四个域合计 74 个（Workspace 24、Slack 11、Travel 28、Banking 11）。")
qa("问：论文里说 70 个工具，你们说 74 个？",
   "答：论文正文写的是 74，表 1 的标题写 70，但表里各行相加是 74——这是论文的一处笔误，以 74 为准。")
qa("问：如果换一个域，你们的代码要改吗？",
   "答：读取和渲染不用改，但要给新域的工具补对象映射表；不补的话，那些工具的“对象检查”会失效。")

step("B. 关于清单本身")
qa("问：清单里为什么不放工具说明（docstring）？",
   "答：这是个取舍，也是个可改进点。论文说 AgentDojo 原版会把工具文档放进 prompt；我们只放了名字和参数。"
   "名字清楚的工具不受影响，名字含糊的容易漏列。下一步可以把说明也渲染进去。")
qa("问：只读靠名字前缀判断，可靠吗？",
   "答：不完全可靠，是已知局限。名字里带 get_/read_ 的通常是查询，但如果有写操作起了查询的名字，就会误判。"
   "误判的后果是它自动进 T 并跳过裁判，所以上线前要做工具清单的代码审查。")
qa("问：清单是每轮都给模型吗？",
   "答：不是。解析器只在一个任务开始时调用一次，清单只给这一次。之后每轮的规划器用的是 AgentDojo 自己那套提示，"
   "不经过我们。")
qa("问：74 个工具全塞进去，上下文不会爆吗？",
   "答：不会。每个域只用自己那 11–28 个工具，不是四个域混在一起。渲染后一般只有十几到三十行。")

step("C. 关于提示词")
qa("问：这七条规则是拍脑袋想的吗？",
   "答：不是，每条都对应一次实测失败，文档里都写了具体数字。比如规则 2 的由来是一次净负的实验——"
   "ASR 从 9.52% 升到 11.43%、UA 从 0.40 掉到 0.39，所以回退了。")
qa("问：提示词写这么长，会不会过拟合到某个域？",
   "答：规则是“约束”不是“模板”——它规定“怎么填”，不规定“填什么内容”。换域只换清单，规则不用改。")
qa("问：为什么不干脆让模型自由发挥，你们再筛？",
   "答：因为自由发挥的输出格式不可控，代码没法解析。固定 JSON 是为了让后面的四道校验有东西可校。")
qa("问：温度设 0 有什么代价？",
   "答：输出更死板，遇到措辞模糊的请求时不会“多想一步”。这是用灵活性换可复现性——解析结果要当判定基准，"
   "同一句话两次解析不同就没法复现。")

step("D. 关于模型怎么挑工具")
qa("问：模型怎么知道“付房租”要用 send_money？",
   "答：靠语义对齐，不是查表。工具名本身是英文短语，模型预训练时见过无数次“send money=转账”；"
   "再加上参数名 recipient/amount 的提示，它就能把“付”和 send_money 接上。")
qa("问：如果工具名字起得不好会怎样？",
   "答：对不上，可能漏列。所以工具命名很重要，这也是为什么现在的大模型工具都要求“名字即语义”。")
qa("问：模型多列了工具，是不是就危险了？",
   "答：不危险。T 只是“允许动用”，多列不等于会调用；而且就算调用，O 和 P 还会逐项核对对象和来源。"
   "真正危险的是漏列——任务做不完。")

step("E. 和论文、和 IPIGuard 的关系")
qa("问：这套东西和 IPIGuard 的 TDG 有什么区别？",
   "答：都是“提示词定义格式 + 代码解析”，都不训练。区别在判定对象：它的图判“工具在不在计划里”，"
   "我们判“每个参数值的来源”。它管工具准入，我们管值准入。")
qa("问：你们这套算创新吗？",
   "答：清单本身不是创新，是基础设施。创新在它支撑的判定——把判定从工具名下沉到参数值的来源。"
   "清单的价值是让“对象”这个概念可计算（哪个参数是作用对象）。")

step("F. 关于局限")
qa("问：这套办法最脆弱的地方在哪？",
   "答：三处。一是对象映射表靠人工，漏一条该工具就没有对象检查；二是只读靠命名推断，可能误判；"
   "三是清单没给工具说明，名字含糊时模型容易漏列。")
qa("问：如果攻击者知道了你们的清单，能绕过吗？",
   "答：清单是公开的，绕过不靠清单。绕过要看判定——它要能骗过“每个值都有合法来源”这条，"
   "而这正是我们真实失败案例暴露的那类问题（值合法但角色错位）。")

# ------------------------------------------------------------------ 五
heading("五、答辩口径：三句话")

para("如果时间只够说三句：")
para("第一句：清单不是我们编的，是环境给的函数签名，加两张人工映射表。", space_before=4)
para("第二句：提示词的每一条规则，都是从一次实测失败里长出来的。")
para("第三句：模型只负责按清单填空，填完的草稿要过四道代码校验，才成为授权范围。")

doc.add_paragraph()
para("附：需要现场演示时，可直接用银行域例子——用户说“把 10 月房租付给房东 UK1234…，金额按账单 bill.pdf 的合计”，"
     "清单四行、输出一段 JSON、四道校验，两分钟能讲完。")

out = os.path.join(HERE, "工具清单与提示词的来历-逐节精讲.docx")
doc.save(out)
print("saved:", out, os.path.getsize(out), "bytes")
