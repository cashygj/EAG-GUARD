# -*- coding: utf-8 -*-
"""大模型如何解析用户指令：机制、参数与是否需要训练。

独立成文，只回答三个问题：
1) 大模型从底层是怎么“解析”用户指令的；
2) 我们实验用的模型内部参数是什么；
3) 解析这一步需不需要训练大模型，为什么不需要。
"""
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
SONG = "宋体"
HEI = "黑体"
NAVY = RGBColor(0x16, 0x28, 0x3F)
TEAL = RGBColor(0x0F, 0x76, 0x6E)
GREY = RGBColor(0x5B, 0x6B, 0x7C)
RED = RGBColor(0xC0, 0x39, 0x2B)

doc = Document()
normal = doc.styles["Normal"]
normal.font.name = SONG
normal.font.size = Pt(11)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), SONG)
normal.paragraph_format.line_spacing = 1.42
normal.paragraph_format.space_after = Pt(4)

for sec in doc.sections:
    sec.top_margin = Cm(2.1)
    sec.bottom_margin = Cm(2.1)
    sec.left_margin = Cm(2.4)
    sec.right_margin = Cm(2.4)


def _set(run, size, bold=False, color=None, font=SONG):
    run.font.size = Pt(size)
    run.bold = bold
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    if color is not None:
        run.font.color.rgb = color


def para(parts, size=11, indent=0.0, space_before=0, space_after=4):
    par = doc.add_paragraph()
    fmt = par.paragraph_format
    fmt.line_spacing = 1.42
    fmt.space_before = Pt(space_before)
    fmt.space_after = Pt(space_after)
    if indent:
        fmt.left_indent = Cm(indent)
    for text, bold, color, font in parts:
        run = par.add_run(text)
        _set(run, size, bold, color, font)
    return par


def plain(text, size=11, color=None, bold=False, indent=0.0, space_before=0, space_after=4):
    return para([(text, bold, color, SONG)], size, indent, space_before, space_after)


def h1(text, size=13.5):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(14)
    par.paragraph_format.space_after = Pt(5)
    run = par.add_run(text)
    _set(run, size, True, NAVY, HEI)
    return par


def h2(text, size=11.8):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(9)
    par.paragraph_format.space_after = Pt(3)
    run = par.add_run(text)
    _set(run, size, True, TEAL, HEI)
    return par


def bullet(parts, size=10.5, indent=0.95):
    par = doc.add_paragraph()
    fmt = par.paragraph_format
    fmt.left_indent = Cm(indent)
    fmt.first_line_indent = Cm(-0.45)
    fmt.space_after = Pt(2)
    fmt.line_spacing = 1.38
    run = par.add_run("· ")
    _set(run, size)
    for text, bold, color, font in parts:
        r = par.add_run(text)
        _set(r, size, bold, color, font)
    return par


def block(lines, size=9.3, shade_hex="F2F5F7"):
    for i, ln in enumerate(lines):
        par = doc.add_paragraph()
        fmt = par.paragraph_format
        fmt.left_indent = Cm(0.8)
        fmt.space_before = Pt(2 if i == 0 else 0)
        fmt.space_after = Pt(0)
        fmt.line_spacing = 1.2
        run = par.add_run(ln)
        _set(run, size, False, RGBColor(0x24, 0x34, 0x47))
        pPr = par._p.get_or_add_pPr()
        shd = pPr.makeelement(qn("w:shd"), {})
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), shade_hex)
        pPr.append(shd)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def shade_cell(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.makeelement(qn("w:shd"), {})
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def table(headers, rows, widths, size=9):
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
r = par.add_run("大模型如何解析用户指令")
_set(r, 19, True, NAVY, HEI)

par = doc.add_paragraph()
par.alignment = WD_ALIGN_PARAGRAPH.CENTER
par.paragraph_format.space_after = Pt(3)
r = par.add_run("—— 底层机制、内部参数，以及“要不要训练”")
_set(r, 11, False, GREY)

par = doc.add_paragraph()
par.alignment = WD_ALIGN_PARAGRAPH.CENTER
par.paragraph_format.space_after = Pt(12)
r = par.add_run("以 EAG-Guard 的任务解析器为例，模型为 qwen3.5-27b")
_set(r, 9.5, False, GREY)

plain("这份文档只回答三个问题：模型从底层是怎么“解析”一句话的；它内部的参数是什么；"
      "以及解析这一步需不需要训练。全文用同一个例子贯穿：")

block(["用户请求：“把 10 月房租付给房东，账号 UK12345678901234567890，",
       "           金额按账单 bill.pdf 里的合计。”",
       "系统把它和工具清单一起送给模型，要求输出一段 JSON：",
       "           {\"tools\":[…], \"objects\":{…}, \"params\":{…}}"], size=9.5)

# ------------------------------------------------------------------ 一
h1("一、大模型是怎么“解析”用户指令的")

h2("1.1 先说结论：它没有“解析模块”")
para([("大模型内部没有词法分析、句法分析、语义解析这些模块。", False, None, SONG),
      ("它做的只有一件事：给定前面所有的文字，预测下一个 token 是什么。", True, NAVY, SONG)])
plain("我们说的“解析用户指令”，在模型侧的真实过程是：把它读成一段前缀，"
      "然后一个 token 一个 token 地续写出一段 JSON；再由代码把这段 JSON 裁成合法的授权范围。")

h2("1.2 六步流水线")
table(["步骤", "做什么", "这句话经过时发生了什么"],
      [["① 拼输入", "把系统提示、工具清单、用户请求拼成一个字符串", "形成“【工具清单】…【用户请求】把 10 月房租…”这一段前缀"],
       ["② 分词", "按分词表切成 token，每个 token 换成一个整数 id", "“把”“10”“月”“房租”……变成几十个 id"],
       ["③ 嵌入", "每个 id 查一张大表，得到一个向量", "每个 token 变成 5,120 个浮点数"],
       ["④ 过 64 层", "注意力让词与词互相看，前馈网络提供知识", "“金额”强烈关注“按账单的合计”"],
       ["⑤ 输出层", "最后一层的向量乘大矩阵，得到词表上每个 token 的分数", "得到 248,320 个分数"],
       ["⑥ 解码", "按规则挑一个 token 接回前缀，回到第 ④ 步", "温度 0 时每次取分数最高的那个"]],
      widths=[2.2, 6.8, 6.8])

h2("1.3 前两步用具体数字看")
table(["环节", "本例", "说明"],
      [["分词表大小", "248,320", "模型认识的全部 token 数量（qwen3.5-27b 的 vocab_size）"],
       ["一句话的 token 数", "约 30 个", "中文常一字一 token，数字和英文会被拆成若干段"],
       ["嵌入维度", "5,120", "每个 token 表示成 5,120 维的向量"],
       ["嵌入表大小", "248,320 × 5,120 ≈ 12.7 亿参数", "这张表本身就是一个“参数大户”"]],
      widths=[3.6, 6.6, 5.6])
para([("注意：", True, RED, SONG),
      ("上面“约 30 个 token”只是示意。具体怎么切取决于分词表，同一个词在不同模型里可能被切成不同段。",
       False, None, SONG)], space_before=2)

h2("1.4 第④步：64 层里在发生什么")
plain("qwen3.5-27b 的 64 层不是同一种结构，而是两种交替：")
table(["层类型", "层数", "作用", "关键尺寸"],
      [["线性注意力", "48 层", "便宜、缓存不随长度增长，承担大部分计算", "key 16 头×128 维；value 48 头×128 维"],
       ["全注意力", "16 层（每 4 层插一个）", "负责长距离检索，让远处的信息能对上", "24 个 Q 头；4 个 KV 头；每头 256 维"],
       ["前馈网络", "每层之后都有", "存事实性知识（“房租通常付给房东”）", "5,120 → 17,408 → 5,120"]],
      widths=[3.0, 3.0, 5.4, 4.4])
para([("粗浅地说：", False, None, SONG),
      ("注意力决定“这个位置该看前文的哪些位置”，前馈网络提供“这个模式通常意味着什么”。"
       "所谓“理解”，是这两者叠加出来的效果，不是某一行代码写死的规则。", False, None, SONG)],
     space_before=2)

h2("1.5 第⑥步：为什么输出能变成 JSON")
plain("模型本来只是续写文字。我们让它输出 JSON，靠的是三件事：")
bullet([("提示词里的格式约定：", True, None, SONG),
        ("明确写出“只输出 JSON，字段名是 tools / objects / params”。模型见过大量 JSON，照格式续写最省力。", False, None, SONG)])
bullet([("温度设为 0：", True, None, SONG), ("每一步都取概率最高的 token，输出尽量稳定，不花样翻新。", False, None, SONG)])
bullet([("失败重试：", True, None, SONG),
        ("万一输出不是合法 JSON，就把“输出无法解析，请只输出那个 JSON 对象”追加回去，再试一次；"
         "仍失败则退化成保守范围。", False, None, SONG)])
para([("所以真正发生的事情是：", True, NAVY, SONG),
      ("模型“续写”出一段像授权范围的文字；代码把它解析、裁剪、校验，才变成程序里的授权范围对象。",
       False, None, SONG)], space_before=2)

# ------------------------------------------------------------------ 二
h1("二、我们实验用的大模型，内部参数是什么")

h2("2.1 两个模型")
table(["模型", "类型", "参数量", "运行记录条数"],
      [["qwen-plus-2025-04-28", "闭源 API（阿里）", "官方未公开", "18,250"],
       ["qwen3.5-27b", "开源，Apache-2.0", "26.9B", "3,822"]],
      widths=[5.2, 5.0, 3.2, 3.0])
plain("运行记录里还单独记了解析器与裁判所用的模型（scope_model / judge_model），"
      "说明这两步可以独立选型，也有据可查。")

h2("2.2 26.9B 个参数都在哪")
table(["部分", "参数量", "怎么算出来的"],
      [["词嵌入表", "约 12.7 亿", "248,320 × 5,120"],
       ["输出头", "约 12.7 亿", "配置里 tie_word_embeddings = false，不与嵌入共享"],
       ["64 层（注意力 + 前馈）", "约 220 亿", "每层约 3.4 亿（其中前馈层约 2.67 亿）"],
       ["合计", "26.9B（官方口径）", "与上面估算量级一致"]],
      widths=[4.6, 4.4, 7.0])
plain("换算成显存：bf16 每参数 2 字节，约 54GB；4bit 量化后约 17GB，单张 24GB 显卡即可运行。")

h2("2.3 关键配置一览（公开可查）")
table(["配置项", "取值", "意味着什么"],
      [["hidden_size", "5,120", "每层的表示宽度"],
       ["num_hidden_layers", "64", "层数"],
       ["num_attention_heads", "24", "全注意力层的 Query 头数"],
       ["num_key_value_heads", "4", "GQA：6 个 Query 头共享 1 组 KV，省显存"],
       ["head_dim", "256", "每个注意力头的维度"],
       ["intermediate_size", "17,408", "前馈网络的中间宽度"],
       ["vocab_size", "248,320", "分词表大小"],
       ["max_position_embeddings", "262,144", "上下文长度 256K"]],
      widths=[5.4, 4.0, 6.6])

h2("2.4 “参数”有两种意思，别混")
table(["", "是什么", "会不会随调用变化", "我们怎么设"],
      [["模型参数（权重）", "模型里的浮点数矩阵，决定它的能力", "固定，训练完就不变", "不设，直接用"],
       ["推理超参", "每次调用时传的几个数", "每次都可以不同", "temperature = 0"]],
      widths=[4.0, 6.4, 3.4, 3.4])
plain("推理超参里最要紧的是温度：0 表示每步都取概率最高的 token（贪心解码），"
      "这样同一句话两次解析的结果才尽量一致。温度不为 0 时才会用到 top_p / top_k 这类采样参数。")

h2("2.5 为什么这些数字对我们重要")
bullet([("可复现：", True, None, SONG),
        ("解析结果要当整条判定链的基准，模型一旦换版本，T/O/P 就可能变，所以记录里写的是带日期的快照名。", False, None, SONG)])
bullet([("成本：", True, None, SONG),
        ("解析每个任务只调用一次，26.9B 这一档的单次成本远低于几百 B 的模型。", False, None, SONG)])
bullet([("选型：", True, None, SONG),
        ("换模型的收益主要体现在规划与执行，解析这一步对模型强弱不敏感——它只做信息抽取。", False, None, SONG)])

# ------------------------------------------------------------------ 三
h1("三、解析用户指令需要训练大模型吗")

h2("3.1 结论：不需要")
para([("解析这一步是零训练的：", True, NAVY, SONG),
      ("用现成模型 + 提示词 + 代码校验即可，不做任何微调，也不训练新的解析器。", False, None, SONG)])

h2("3.2 为什么不需要：四条理由")
bullet([("任务性质是信息抽取，不是能力习得。", True, None, SONG),
        ("把一句话拆成“用哪些工具、作用在谁、哪个参数照材料填”，是模型预训练阶段就学过的能力，"
         "零样本就能做，不需要教。", False, None, SONG)])
bullet([("换域成本不划算。", True, None, SONG),
        ("每个任务域的工具名、措辞都不一样，训一个换一个；而提示词加规则是随域改配置，不动模型。", False, None, SONG)])
bullet([("训练改变不了它“按概率续写”的本质。", True, None, SONG),
        ("微调只是让某种输出更常见，仍然可能出错；真正保证正确性的是输出的结构化校验。", False, None, SONG)])
bullet([("安全性不押在解析器上。", True, None, SONG),
        ("就算 T/O/P 解析偏了，后面还有逐参数溯源与独立裁判；解析是入口，不是最后一道防线。", False, None, SONG)])

h2("3.3 不训练，靠什么保证质量")
plain("靠模型外面这一圈代码。模型给出的结果要过四道关：")
table(["关卡", "做什么", "为什么需要"],
      [["白名单", "工具名必须在工具清单里，不在的直接丢弃", "防模型凭记忆编造不存在的工具"],
       ["只读工具默认放行", "读取类工具直接进 T，不让模型逐个点名", "实测让模型点名会漏，换个检索路径就被误判"],
       ["动作词兜底", "请求里有“付/删/发/改”时把对应工具补进 T", "只补 T，不放松对象与来源约束"],
       ["敏感参数强制字段型", "金额、收款人、账号、URL 不接受正文匹配", "这些字段决定钱给谁、东西送到哪"]],
      widths=[3.6, 6.4, 6.6])
plain("另外还有一道兜底：解析失败（JSON 不合法、调用超时）时，授权范围退化为“只有只读工具”，"
      "宁可少做，不可越权。")

h2("3.4 什么情况下才值得训练")
plain("以下三种情形才考虑微调，而且都不是当前的问题：")
bullet([("要把解析换成很小小的本地模型：", True, None, SONG), ("用大量标注样本蒸馏，换成本与隐私。", False, None, SONG)])
bullet([("输出格式老是不稳：", True, None, SONG), ("比起微调，更省事的做法是约束解码或加重试。", False, None, SONG)])
bullet([("某个域有大量专有措辞：", True, None, SONG), ("先用规则与辞书覆盖，仍然不够再考虑微调。", False, None, SONG)])
para([("代价也要说清楚：", True, RED, SONG),
      ("微调需要标注数据、要维护版本、换域要重训，而且一旦模型更新还得重来；"
       "在“解析只是入口”的前提下，这些投入换不来等价的收益。", False, None, SONG)], space_before=2)

h2("3.5 一个对照：规则解析器与模型解析器并存")
plain("代码里其实有两个实现，接口相同（ScopeParser），可以互换：")
table(["实现", "怎么工作", "优点", "缺点"],
      [["规则版", "正则 + 辞书，匹配金额、账号、文件名、委托措辞", "确定、零成本、可解释", "换域要重写，召回有限"],
       ["模型版", "一次 LLM 调用输出 JSON，再由代码裁剪", "泛化好，换域只改提示词", "有调用成本，输出需校验"]],
      widths=[2.6, 6.2, 4.0, 3.8])
plain("实验里以模型版为主，规则版作为基线与兜底——这也是“不需要训练”的另一层含义："
      "接口固定，随时可以换成更便宜或更可控的实现，而不必动整个方法。")

# ------------------------------------------------------------------ 四
h1("四、三问三答")
table(["问题", "回答"],
      [["大模型怎么解析指令", "它不解析，只续写。分词→嵌入→64 层→输出概率→逐 token 生成 JSON，"
                        "再由代码把 JSON 裁成授权范围。"],
       ["内部参数是什么", "权重共 26.9B：嵌入 12.7 亿 + 输出头 12.7 亿 + 64 层约 220 亿；"
                     "另有调用时传的推理超参（temperature 等）。"],
       ["需要训练吗", "不需要。零训练，靠提示词 + 四道代码校验 + 失败兜底；"
                 "安全性由后续的溯源与裁判承担，不押在解析器上。"]],
      widths=[4.2, 11.6])

doc.add_paragraph()
para([("一句话收束：", True, NAVY, SONG),
      ("模型内部是几十亿个浮点数在算“下一个词最可能是什么”；我们做的事，是给这段续写套上格式（JSON）、"
       "压低随机性（温度 0）、再用代码把不合法的部分裁掉。", False, None, SONG)], space_after=2)

out = os.path.join(HERE, "大模型解析机制与参数.docx")
doc.save(out)
print("saved:", out, os.path.getsize(out), "bytes")
