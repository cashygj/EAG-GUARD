# -*- coding: utf-8 -*-
"""授权范围的解析方法（压缩版：四步）。"""
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
        fmt.left_indent = Cm(0.9)
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


# ==================================================================
title("授权范围的解析方法")
sub("—— 模型没训练过，T、O、P 是怎么来的")

# ------------------------------------------------------------------ 一
heading("一、模型是怎么得出 T、O、P 的")

para("模型没有被训练过，也没有被微调。它能得出 T、O、P，靠三样东西：提示词里给了模板，"
     "运行时给了素材，填完由代码核对。模板写在系统提示里——T 是允许调用的工具，O 是允许作用的对象，"
     "P 是每个参数的取值来源；素材是工具清单和用户那句话，每次调用现给，不在模型脑子里。")

para("模型给的只是草稿，要过四道核对才算数：工具名必须在清单里、只读工具默认补全、"
     "用户说了“付/删/发”就把对应工具补上、金额收款人这类值只能取材料里的字段。"
     "草稿不合规就改掉，连 JSON 都输出不对就退成只读范围。")

para("所以模型负责填表，表是我们画的；它给草稿，我们定终稿。这也是不需要训练的原因——"
     "训练能提高草稿的质量，但改不了“终稿由代码说了算”。")

# ------------------------------------------------------------------ 二
heading("二、解析过程：四步")

step("S1　准备材料：把用户的话和工具清单拼起来")
para("系统把工具清单整理成几行文字，和用户原话一起放进请求里。只放用户的话，不放任何工具返回的内容——"
     "一旦读了外部内容，解析就可能被污染。")

step("S2　让模型填表：一次调用，输出一段 JSON")
para("请求发给模型，让它输出固定格式的 JSON，里面三块：用哪些工具、作用在谁身上、哪个参数照哪份材料填。"
     "温度设成 0，让它别自由发挥。模型只看得到这段请求，看不到规划器的想法，也看不到工具返回的原文。")

step("S3　核对草稿：T、O、P 各查一遍")
para("拿到的草稿逐项核对。T：清单里没有的工具删掉；只读工具默认补进来；用户说了“付/删/发/改”，"
     "就把对应的写操作工具补上。O：检查对象类别，把网址、文件名统一写法（去 http、去 www、去结尾斜杠），"
     "列表参数要求每一项都在名单里，长得像授权域名的按仿冒处理。P：模型说“金额照账单填”就记一条委托；"
     "金额、收款人、账号这类敏感参数强制成字段型，只认材料里的字段值，正文里的同样数字不算。")

para("四道核对之后仍不合格，或者 JSON 根本抠不出来，就退一步：只给只读工具，O 留空。"
     "任务可能做不完，但不会做错事；这个状态单独记录，以便和“模型判的就是只读”区分开。")

step("S4　定稿入图：任务期间不许改")
para("把核对后的结果定死（程序上不可修改），同时在图上登记：用户请求、授权、工具、对象、委托各是一个点，"
     "用线连起来。后面每次动作判定，就是顺着这些线往回查“这个值是谁给的”。")

# ------------------------------------------------------------------ 三
heading("三、走一遍这笔转账")

para("用户说：「把 10 月房租付给房东，账号 UK12345678901234567890，金额按账单 bill.pdf 里的合计。」")

para("S1 交给模型的两样东西：", space_before=4, space_after=2)
code("""
【工具清单】
- read_file（只读）：参数 [name]，对象类别=file
- send_money（有副作用）：参数 [recipient, amount, subject]，对象类别=recipient
- send_email（有副作用）：参数 [recipients, subject, body]，对象类别=recipient

【用户请求】
把 10 月房租付给房东，账号 UK12345678901234567890，金额按账单 bill.pdf 里的合计。
""")

para("S2 模型填出来的草稿：", space_before=4, space_after=2)
code("""
{
  "tools": ["read_file", "send_money"],
  "objects": {"recipient": ["UK12345678901234567890"],
              "file": ["bill.pdf"]},
  "delegations": [
    {"tool": "send_money", "param": "amount", "source": "file", "mode": "field"}
  ],
  "notes": "用户要求按账单合计付款"
}
""")

para("S3 核对后得到的结果：", space_before=4, space_after=2)
table(["对象", "草稿里是什么", "核对做了什么", "最后结果"],
      [["T", "read_file, send_money", "名字都在清单里；只读工具已含；按“付”“账单”补命令工具",
        "{读文件, 转账}（发邮件没被补进来）"],
       ["O", "recipient, file", "类别对；取值格式统一",
        "{收款人: UK1234…，文件: bill.pdf}"],
       ["P", "金额委托给 file", "记一条金额委托；收款人按默认规则；敏感参数设字段型",
        "金额只取账单字段；收款人只能用户给"]],
      widths=[1.2, 4.6, 7.0, 5.2])

para("S4 定稿后，图上的样子：", space_before=4, space_after=2)
code("""
用户请求 ──授予──▶ 授权:收款人 UK1234… ──支撑──▶ 对象:UK1234…
用户请求 ──声明委托──▶ 委托:金额←账单
""")

para("后面判定时，就看金额这个值能不能顺着线走回“委托”和“用户请求”：走得通就是用户给的；"
     "只走得到账单正文那条证据、走不回用户，那就是注入。")

para("这四步里，模型只出现在 S2 这一处，其余三步都是代码在干。所以换一个模型，T、O、P 的形态都不变，"
     "变的只是草稿的质量。", bold=True)

out = os.path.join(HERE, "授权范围解析方法.docx")
doc.save(out)
print("saved:", out, os.path.getsize(out), "bytes")
