# -*- coding: utf-8 -*-
"""S1：智能体与工具集（按导师 S1.docx 的体例扩写）。"""
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
    sec.top_margin = Cm(2.4)
    sec.bottom_margin = Cm(2.4)
    sec.left_margin = Cm(2.7)
    sec.right_margin = Cm(2.7)


def _set(run, size, bold=False, font=SONG):
    run.font.size = Pt(size)
    run.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)


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
                align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)


def heading(text, size=14):
    return para(text, indent=False, size=size, bold=True, font=HEI,
                space_before=15, space_after=6)


def sub(text, size=12):
    return para(text, indent=False, size=size, bold=True, font=HEI,
                space_before=10, space_after=3)


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
title("S1　智能体与工具集")

# ------------------------------------------------------------------ 一
heading("一、智能体的构成")

para("本方法所用智能体由三部分组成：一个大语言模型、一组工具、一个循环控制器。")

table(["组成", "作用", "在本实验中的对应"],
      [["大语言模型", "读上下文，决定“下一步调哪个工具、参数填什么”", "qwen3.5-27b（开源）、qwen-plus-2025-04-28（闭源 API）"],
       ["工具", "真正操作环境：转账、读文件、发邮件、订酒店", "四个应用域共 74 个工具"],
       ["循环控制器", "把模型输出变成工具调用，把结果写回上下文，再进入下一轮，直到模型不再请求工具",
        "ReAct 循环，最多若干轮"]],
      widths=[3.0, 7.6, 5.8])

para("一次任务按如下顺序执行：")

para("第一步，把系统提示、用户任务与工具清单一起送入大语言模型；第二步，模型输出若干工具调用请求，"
     "每个请求包含工具名与参数；第三步，循环控制器依次执行这些调用，工具读写环境状态；"
     "第四步，把工具返回结果写回上下文，再次送入模型；第五步，模型不再请求工具时，输出最终回答。")

para("上述循环中，模型始终只能“提议”调用，调用是否真正执行由外部控制器决定。")

sub("本实验使用的模型")
table(["模型", "类型", "用途"],
      [["qwen3.5-27b", "开源（Apache-2.0，26.9B 参数）", "主实验"],
       ["qwen-plus-2025-04-28", "闭源 API", "对照与早期实验"],
       ["GPT-4o-mini", "闭源 API", "与 IPIGuard 对齐的基线"]],
      widths=[5.0, 6.4, 5.0])
para("所有模型均以温度 0 调用，以保证同一输入得到同一输出。")

sub("本实验采用的智能体")
para("本实验直接采用 AgentDojo 基准自带的 ReAct 式智能体，不对其结构与提示词作任何改动："
     "系统提示、用户任务与工具清单一起送入模型；模型输出一批工具调用；执行器依次执行并把结果写回上下文；"
     "最多循环 15 轮，直到模型不再请求工具为止。守卫不改变这一循环，只是把执行器包了一层，"
     "因此有无防御两支的差别仅在“调用有没有被拦”。")

# ------------------------------------------------------------------ 二
heading("二、步骤S1：获取智能体，构建工具集")

para("步骤S1：获取智能体，构建工具集，所述工具集包含多个工具，每个工具包括工具名、参数表、工具说明、"
     "工具性质和环境依赖；所述工具名用于标识工具；所述参数表用于声明调用工具时所需的参数及数据类型；"
     "所述工具说明用于描述工具的用途；所述工具性质分为只读与有副作用两种，只读表示调用该工具不修改"
     "当前的环境状态，有副作用表示调用该工具会修改环境状态；所述环境依赖指工具所操作的对象，"
     "例如银行账户、邮箱等。")

sub("五个字段的含义")
table(["字段", "含义", "以转账工具为例"],
      [["工具名", "唯一标识一个工具", "send_money"],
       ["参数表", "调用时要填哪些参数、各是什么类型", "recipient（字符串）、amount（数字）、subject（字符串）、date（字符串）"],
       ["工具说明", "一句话描述这个工具干什么", "向收款人发起一笔转账"],
       ["工具性质", "只读 / 有副作用", "有副作用（会新增一条转账记录）"],
       ["环境依赖", "工具操作的那个对象，由系统注入，不需要模型填写", "银行账户（余额、IBAN、流水记录）"]],
      widths=[2.6, 6.6, 7.2])

para("上述五个字段均来自工具本身，不需要另行编写：工具名取自函数名，参数表由参数的类型标注自动生成，"
     "工具说明取自函数的文档字符串，环境依赖由依赖声明指定。")

# ------------------------------------------------------------------ 三
heading("三、工具库的情况")

para("工具库按应用域划分，每个应用域对应一类真实产品：银行、办公套件、团队协作、旅行预订。"
     "四个应用域合计 74 个工具。")

table(["应用域", "工具数", "其中只读", "其中有副作用", "代表工具"],
      [["银行（banking）", "11", "6", "5", "send_money、read_file、update_password"],
       ["办公（workspace）", "24", "14", "10", "send_email、create_calendar_event、share_file"],
       ["协作（slack）", "11", "5", "6", "send_direct_message、read_channel_messages、post_webpage"],
       ["旅行（travel）", "28", "22", "6", "reserve_hotel、reserve_car_rental、get_hotels_prices"],
       ["合计", "74", "47", "27", "—"]],
      widths=[4.2, 2.2, 2.4, 2.8, 5.4])

para("按性质分：只读工具 47 个，有副作用工具 27 个。只读工具用于查询，不改变环境状态；"
     "有副作用工具用于写入，是攻击的主要目标。")

sub("环境依赖举例")
table(["应用域", "环境依赖（工具操作的对象）"],
      [["银行", "银行账户：余额、账号、流水记录"],
       ["办公", "邮箱、日历、云盘"],
       ["协作", "频道与消息、用户列表、网页"],
       ["旅行", "酒店、餐厅、租车公司与预订记录"]],
      widths=[3.4, 12.4])

para("环境依赖由系统在调用时自动注入，不进入参数表，因此不向模型暴露。")

# ------------------------------------------------------------------ 四
heading("四、小结")

para("智能体由模型、工具与循环控制器组成；工具集是环境提供的能力集合，每个工具由工具名、参数表、"
     "工具说明、工具性质与环境依赖五项构成；四个应用域合计 74 个工具，其中只读 47 个、有副作用 27 个。")

para("上述工具集在任务开始前由环境注册，其内容不来源于用户请求。")

out = os.path.join(HERE, "S1-智能体与工具集-修订.docx")
doc.save(out)
print("saved:", out, os.path.getsize(out), "bytes")
