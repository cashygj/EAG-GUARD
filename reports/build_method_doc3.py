# -*- coding: utf-8 -*-
"""方法说明（对齐 2.docx 的语气与体例）。

体例要点：
- 每步以「Sn：步骤名：」开头，写成一句以分号收尾的完整表述；
- 其后用「所述……」段落补充定义、边界与例外；
- 全篇用书面语，不出现口语、不用项目符号。
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

doc = Document()
normal = doc.styles["Normal"]
normal.font.name = SONG
normal.font.size = Pt(12)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), SONG)
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(6)

for sec in doc.sections:
    sec.top_margin = Cm(2.5)
    sec.bottom_margin = Cm(2.5)
    sec.left_margin = Cm(2.8)
    sec.right_margin = Cm(2.8)


def para(text, indent=True, size=12, bold=False, color=None, font=SONG,
         align=None, space_before=0, space_after=6):
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
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    if color is not None:
        run.font.color.rgb = color
    return par


def title(text, size=19):
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_before = Pt(6)
    par.paragraph_format.space_after = Pt(12)
    run = par.add_run(text)
    run.bold = True
    run.font.size = Pt(size)
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), HEI)
    return par


def heading(text, size=13.5):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(14)
    par.paragraph_format.space_after = Pt(6)
    run = par.add_run(text)
    run.bold = True
    run.font.size = Pt(size)
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), HEI)
    return par


def shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.makeelement(qn("w:shd"), {})
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def table(headers, rows, widths, size=9.5):
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
        r.bold = True
        r.font.size = Pt(size)
        r.font.name = "Times New Roman"
        r._element.rPr.rFonts.set(qn("w:eastAsia"), HEI)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shade(c, "16404D")
    trPr = t.rows[0]._tr.get_or_add_trPr()
    trPr.append(trPr.makeelement(qn("w:tblHeader"), {}))
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(size)
            r.font.name = "Times New Roman"
            r._element.rPr.rFonts.set(qn("w:eastAsia"), SONG)
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
title("基于授权不变式的智能体注入防御方法")

para("本方法以用户指令为唯一可信输入，在执行每个动作之前判定该动作的参数取值是否仍在用户授权范围之内；"
     "外部内容可以改变任务的执行计划，但不能改变用户授权。", size=10.5,
     color=RGBColor(0x5B, 0x6B, 0x7C), space_after=10)

heading("一、方法步骤")

steps = [
    ["S1：任务解析：仅以用户指令为输入，解析生成授权范围 A=(T, O, P)；所述 T 为允许调用的工具集合，"
     "O 为允许作用的对象集合，P 为参数来源约束，用于限定该参数值取自用户直接指定、或由用户指定的来源在运行时取值；"
     "所述解析不读取任何工具响应，所得授权范围在任务执行期间保持不变；",
     "所述来源约束分为字段型与内容型两类：字段型要求取值等于被指定来源的结构化字段值，"
     "同一来源正文中的同形字符串不构成授权；内容型允许取值与该来源的文本内容相匹配，用于转发、摘要等以内容为目标的参数。",
     "所述“由用户指定的来源在运行时取值”以委托表示：委托记录字段与来源的对应关系，并由用户指令指向该委托，"
     "该委托作为后续溯源判定的终止节点之一。"],

    ["S2：证据切片：每次工具调用返回后，将工具响应切分为一条或多条证据，并为每条证据标注来源、可信标记与结构化字段；"
     "所述可信标记按来源划分，仅用户指令与系统提示为可信，工具响应均为不可信；"
     "所述结构化字段由按工具类型预设的抽取规则得到，不依赖模型推断；",
     "所述结构化字段与证据正文分别存储：当字段无法抽取时，该证据不提供相应字段，后续判定按无法归因处理，"
     "不得以正文中的同形内容替代该字段。"],

    ["S3：构建授权—证据—动作图：以用户指令、授权、委托、证据、参数、动作为六类节点构建有向图，"
     "所述参数节点对应动作的每一个实参取值；所述有向图包含五类边，即用户指令指向授权的授予边、"
     "用户指令指向委托的声明委托边、授权或证据指向参数的支撑边、委托指向参数的派生边、"
     "以及动作指向其所产出证据的产出边；",
     "所述有向图按增量方式构建：每一轮仅新增本轮的动作节点、参数节点与所产生或被引用的证据节点，"
     "判定仅针对该增量中的参数节点进行，不对全图重新计算。"],

    ["S4：字段级溯源判定：对动作的每一个参数值，自其参数节点出发，仅沿支撑边与派生边反向回溯并收集可达的根节点；"
     "若可达用户指令、授权或委托之一，判定该取值来源于用户，放行该参数；若仅可达不可信证据，"
     "判定该取值为注入，拒绝该动作；",
     "所述回溯不沿授予边、声明委托边与产出边进行：前两者用于自用户指令派生授权与委托，不表示取值的来源；"
     "产出边由动作指向证据，若参与回溯，动作将以其自身产出为自己作证。",
     "所述判定为存在性判定：存在至少一个可信根即放行；同一取值同时可达可信根与不可信根时，"
     "不因存在不可信根而直接拒绝，而由下一步的语义裁判复核。",
     "当参数值不能经支撑边或派生边到达任何可信根时，标记为无法归因，按不可信处理。"],

    ["S5：独立语义裁判：将用户指令、授权范围、候选动作及其参数来源以结构化视图提交语义裁判，"
     "由该裁判在不可见规划器自述理由与工具响应原文的条件下，判断该动作是否越权；"
     "所述结构化视图仅包含工具、对象、参数名、参数值及来源类别；",
     "所述判断包括：工具是否属于 T、对象是否属于 O、每一个参数值是否可追溯至授权或委托、"
     "以及是否存在借外部内容扩张授权的行为；任一项不满足即拒绝该动作。",
     "所述语义裁判独立于规划器，以避免被注入内容污染的前提自证。"],

    ["S6：执行、拒绝与输出审核：经判定的动作在执行前重新计算其签名，与判定时的签名逐字一致方予执行；"
     "动作被拒绝时，返回包含可操作原因与可行替代取值的拒绝信息，驱动规划器修改参数后重新判定，"
     "工具响应回写为证据并进入下一轮；最终回答返回前，裁剪其中与不可信证据逐字重合的内容。",
     "所述可操作原因指向具体证据与字段，而非仅声明越权，以便规划器据此修正参数。",
     "所述裁剪以逐字重合长度为依据，不依赖对文本语义的判断，适用于仅通过文本输出传播注入内容的场景。"],
]

for block in steps:
    para(block[0], space_before=8)
    for extra in block[1:]:
        para(extra)

heading("二、与 IPIGuard 方法的步骤对应")

para("下表仅用于说明两者的步骤对应关系：本方法与其在“阻断计划外工具调用”一项上作用相同，"
     "差别在于对同一工具下参数被替换情形的处理。", size=10.5,
     color=RGBColor(0x5B, 0x6B, 0x7C))

table(["本方法", "IPIGuard 对应步骤", "差别"],
      [["S1 任务解析", "S1 构建工具依赖图", "授权范围的来源不同：本方法取自用户指令，对方取自计划结果"],
       ["S2 证据切片", "无", "对方不对工具响应切片，亦无结构化字段的概念"],
       ["S3 建图", "S1 工具依赖图", "本方法的图为增量，节点含参数与证据，边含委托与支撑"],
       ["S4 溯源判定", "S3 的准入检查", "对方判定工具名，本方法判定参数值的来源"],
       ["S5 语义裁判", "无", "对方不设独立判定环节"],
       ["S6 执行与善后", "S5 伪造工具调用", "对方以模拟响应规避错参，本方法拒绝并重新提议"]],
      widths=[3.4, 4.8, 7.6])

out = os.path.join(HERE, "EAG-Guard-方法说明书.docx")
doc.save(out)
print("saved:", out, os.path.getsize(out), "bytes")
