# -*- coding: utf-8 -*-
"""把两张 SVG 图转成 PowerPoint 原生形状，生成 EAG-Guard 配图幻灯片。

为什么不用贴图：python-pptx 不能直接嵌 SVG，贴 PNG 又不可编辑。
这里把 SVG 的元素逐个翻译成 PowerPoint 形状（圆角矩形、直线、任意多边形、
椭圆、文本框），所以打开后每个箭头、每行字都能直接双击修改。

用法： python build_pptx.py
"""
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE as DASH
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
NS = "{http://www.w3.org/2000/svg}"
PX = 9525                      # 96dpi 下 1px = 9525 EMU
FONT = "Microsoft YaHei"


# ----------------------------------------------------------------- 工具
def rgb(value):
    value = (value or "").strip()
    if not value or value == "none":
        return None
    if value.startswith("#"):
        value = value[1:]
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return RGBColor.from_string(value.upper())


def num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def w_of(s, size):
    return sum(size if ord(c) > 0x2E7F else size * 0.56 for c in s)


def set_font(run, size_pt, bold, color, name=FONT):
    f = run.font
    f.size = Pt(size_pt)
    f.bold = bold
    f.color.rgb = color
    f.name = name
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", name)


def no_line(shape):
    shape.line.fill.background()


def polish(shape):
    """去掉主题样式（否则 PowerPoint/LibreOffice 会给形状加默认阴影），
    并显式写入空的 effectLst。"""
    el = shape._element
    style = el.find(qn("p:style"))
    if style is not None:
        el.remove(style)
    spPr = el.find(qn("p:spPr"))
    if spPr is not None and spPr.find(qn("a:effectLst")) is None:
        spPr.append(spPr.makeelement(qn("a:effectLst"), {}))
    return shape


# ----------------------------------------------------------------- 画布
class Canvas:
    """把 SVG 的 px 坐标映射到幻灯片 EMU。"""

    def __init__(self, slide, fig_w, fig_h, box):
        left, top, width, height = box
        self.slide = slide
        self.k = min(width / (fig_w * PX), height / (fig_h * PX))
        self.ox = left + (width - fig_w * PX * self.k) / 2
        self.oy = top + (height - fig_h * PX * self.k) / 2
        self.n = 0
        self.group = ""

    def X(self, px):
        return int(round(self.ox + px * self.k * PX))

    def Y(self, px):
        return int(round(self.oy + px * self.k * PX))

    def L(self, px):
        return int(round(px * self.k * PX))

    def name(self, tag):
        self.n += 1
        return f"{self.group or 'fig'}-{tag}-{self.n}"


def draw_text(cv, el):
    s = el.text or ""
    if not s.strip():
        return
    x, y = num(el.get("x")), num(el.get("y"))
    size = num(el.get("font-size"), 12)
    bold = (el.get("font-weight") or "") == "bold"
    color = rgb(el.get("fill")) or RGBColor(0x24, 0x34, 0x47)
    w = w_of(s, size) + 8
    h = size * 1.34
    box = cv.slide.shapes.add_textbox(
        cv.X(x), cv.Y(y - size * 0.97), cv.L(w), cv.L(h))
    polish(box); box.name = cv.name("t")
    tf = box.text_frame
    tf.word_wrap = False
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = s
    set_font(run, size * cv.k * 0.75, bold, color)


def draw_rect(cv, el):
    x, y = num(el.get("x")), num(el.get("y"))
    w, h = num(el.get("width")), num(el.get("height"))
    rx = num(el.get("rx"))
    fill, stroke = rgb(el.get("fill")), rgb(el.get("stroke"))
    sw = num(el.get("stroke-width"), 1)
    if w >= 1279 and h >= 739:              # 整块白色底，跳过：用幻灯片底色
        return
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if rx > 0 else MSO_SHAPE.RECTANGLE
    shp = cv.slide.shapes.add_shape(shape_type, cv.X(x), cv.Y(y), cv.L(w), cv.L(h))
    polish(shp); shp.name = cv.name("rect")
    if rx > 0:
        try:
            shp.adjustments[0] = min(0.5, rx / max(1.0, min(w, h)))
        except Exception:
            pass
    shp.shadow.inherit = False
    if fill:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    else:
        shp.fill.background()
    if stroke:
        shp.line.color.rgb = stroke
        shp.line.width = Pt(sw * cv.k * 0.75)
        if el.get("stroke-dasharray"):
            shp.line.dash_style = DASH.DASH
    else:
        no_line(shp)


def draw_line(cv, el):
    x1, y1 = num(el.get("x1")), num(el.get("y1"))
    x2, y2 = num(el.get("x2")), num(el.get("y2"))
    color = rgb(el.get("stroke")) or RGBColor(0, 0, 0)
    sw = num(el.get("stroke-width"), 1)
    dash = el.get("stroke-dasharray")
    conn = cv.slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, cv.X(x1), cv.Y(y1), cv.X(x2), cv.Y(y2))
    polish(conn); conn.name = cv.name("line")
    conn.line.color.rgb = color
    conn.line.width = Pt(sw * cv.k * 0.75)
    if dash:
        conn.line.dash_style = DASH.DASH


def _polygon(cv, pts, fill, line_color=None, line_w=0.0, close=True):
    if len(pts) < 2:
        return
    builder = cv.slide.shapes.build_freeform(
        Emu(cv.X(pts[0][0])), Emu(cv.Y(pts[0][1])), scale=1.0)
    builder.add_line_segments(
        [(Emu(cv.X(a)), Emu(cv.Y(b))) for a, b in pts[1:]], close=close)
    shp = builder.convert_to_shape()
    polish(shp); shp.name = cv.name("poly")
    shp.shadow.inherit = False
    if fill:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    else:
        shp.fill.background()
    if line_color:
        shp.line.color.rgb = line_color
        shp.line.width = Pt(line_w * cv.k * 0.75)
    else:
        no_line(shp)


def draw_path(cv, el):
    pts = [(float(a), float(b)) for a, b in
           re.findall(r"[ML]\s*([-\d.]+)[ ,]([-\d.]+)", el.get("d") or "")]
    color = rgb(el.get("stroke")) or RGBColor(0, 0, 0)
    sw = num(el.get("stroke-width"), 1)
    dash = el.get("stroke-dasharray")
    _polygon(cv, pts, None, color, sw, close=False)
    if dash:
        cv.slide.shapes[-1].line.dash_style = DASH.DASH


def draw_polygon(cv, el):
    pts = [(float(a), float(b)) for a, b in
           re.findall(r"([-\d.]+),([-\d.]+)", el.get("points") or "")]
    _polygon(cv, pts, rgb(el.get("fill")), None)


def draw_circle(cv, el):
    cx, cy, r = num(el.get("cx")), num(el.get("cy")), num(el.get("r"))
    shp = cv.slide.shapes.add_shape(
        MSO_SHAPE.OVAL, cv.X(cx - r), cv.Y(cy - r), cv.L(2 * r), cv.L(2 * r))
    polish(shp); shp.name = cv.name("circle")
    shp.shadow.inherit = False
    fill = rgb(el.get("fill"))
    if fill:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    else:
        shp.fill.background()
    no_line(shp)


DISPATCH = {"text": draw_text, "rect": draw_rect, "line": draw_line,
            "path": draw_path, "polygon": draw_polygon, "circle": draw_circle}


def add_figure(slide, svg_path, box):
    root = ET.parse(svg_path).getroot()
    fig_w, fig_h = num(root.get("width")), num(root.get("height"))
    cv = Canvas(slide, fig_w, fig_h, box)
    for el in root.iter():
        tag = el.tag.replace(NS, "")
        if tag == "g":
            cv.group = el.get("id") or cv.group
            continue
        if tag in DISPATCH:
            DISPATCH[tag](cv, el)
    return cv.n


# ----------------------------------------------------------------- 幻灯片
def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def add_cover(prs):
    slide = blank(prs)
    ink = RGBColor(0x16, 0x28, 0x3F)
    muted = RGBColor(0x71, 0x80, 0x8F)
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.42), Inches(0.09), Inches(1.36))
    polish(bar); bar.fill.solid()
    bar.fill.fore_color.rgb = RGBColor(0x2F, 0x55, 0x97)
    no_line(bar)

    tb = slide.shapes.add_textbox(Inches(1.2), Inches(2.3), Inches(11), Inches(0.95))
    tf = tb.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = "证据—授权—动作图"
    set_font(run, 40, True, ink)

    tb2 = slide.shapes.add_textbox(Inches(1.22), Inches(3.28), Inches(11), Inches(0.6))
    p2 = tb2.text_frame.paragraphs[0]
    r2 = p2.add_run()
    r2.text = "六类节点 · 五类边 · 字段级溯源"
    set_font(r2, 20, False, RGBColor(0xA9, 0x76, 0x1A))

    tb3 = slide.shapes.add_textbox(Inches(1.22), Inches(4.06), Inches(11), Inches(0.5))
    p3 = tb3.text_frame.paragraphs[0]
    r3 = p3.add_run()
    r3.text = "外部内容可以改变智能体的计划，但不能改变它的授权"
    set_font(r3, 15, False, muted)

    tb4 = slide.shapes.add_textbox(Inches(1.22), Inches(6.36), Inches(11), Inches(0.4))
    p4 = tb4.text_frame.paragraphs[0]
    r4 = p4.add_run()
    r4.text = "EAG-Guard 阶段性报告答疑 · 2026-11"
    set_font(r4, 12, False, muted)

    notes(slide, "开场一句话：这套图回答的是同一个问题——一个值凭什么能被写进这次动作。")
    return slide


def add_figure_slide(prs, svg, note_text):
    slide = blank(prs)
    margin = Inches(0.16)
    box = (int(margin), int(margin),
           int(prs.slide_width - 2 * margin), int(prs.slide_height - 2 * margin))
    n = add_figure(slide, svg, box)
    notes(slide, note_text)
    return slide, n


def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    add_cover(prs)

    add_figure_slide(
        prs, os.path.join(HERE, "fig1-eag-nodes-edges.svg"),
        "讲图顺序（约 3 分钟）：\n"
        "1. 一句话：这张图回答「一个值凭什么能被写进这次动作」。\n"
        "2. 指中间：所有判定都收敛到「参数」这一个点。\n"
        "3. 指绿路：值从委托来，委托是用户声明的 → 放行。\n"
        "4. 指红路：值只出现在不可信证据里，没人委托它 → 注入，拒绝。\n"
        "5. 指上方：授权范围只从用户请求长出来，这是地基。\n"
        "6. 收尾：外部内容能改计划，改不了授权。\n\n"
        "被问到「六类还是八类」：图上是 8 个框——6 类工作节点（授权、工具、对象、证据、参数、动作）"
        "加 2 个根（用户请求、委托）；代码里节点类型正好 8 个。")

    add_figure_slide(
        prs, os.path.join(HERE, "fig2-eag-instance-fpr.svg"),
        "讲图顺序（约 2 分钟）：\n"
        "1. 同一个工具、同一个参数位（金额），只是取值来源不同。\n"
        "2. 上：金额 9999 只出现在邮件正文里，没人委托 → 注入 → 拒绝。\n"
        "3. 下：金额 98.70 来自账单的结构化字段，用户声明了委托 → 放行。\n"
        "4. 强调：账单本身是不可信的，能用的是它的「字段」，来源是用户的委托。\n"
        "5. 收尾：这不是把 ASR 压小，而是把「同工具换参数」变成可判定的越权。")

    add_figure_slide(
        prs, os.path.join(HERE, "fig3-compare-ipiguard.svg"),
        "讲图顺序（约 2 分钟）：\n"
        "1. 左右两栏是同一个动作：转账（收款人＝房东，金额＝9999）。\n"
        "2. 左边 IPIGuard 只圈「工具」这一格：工具在计划内就放行，参数靠模型估算。\n"
        "3. 右边我们三格全检：金额那一格判出「来源＝注入」→ 拒绝 → 重规划。\n"
        "4. 一句话：差别不在谁拦得多，而在能不能回答「这个值凭什么被写进这次调用」。\n\n"
        "可能被追问「IPIGuard 不是也有伪造工具调用吗」：\n"
        "答：有，但它是提示层偏置——降低模型估错参数的概率，不是对参数值的判定；"
        "它没有「参数值来源」这一表示。这正是对照表第二行。\n"
        "再追问「那凭什么说更好」：25 对同模型切片 5/25 对 1/25 只是方向性；"
        "真正的论据是机制——工具级约束在原理上看不见参数来源。")

    add_figure_slide(
        prs, os.path.join(HERE, "fig4-structure.svg"),
        "讲图顺序（约 2 分钟）：\n"
        "1. 三行是三条流水线，五列是同一副骨架；虚线格＝这一层不存在。\n"
        "2. 无防御有两格空着（没有输入处理，也没有判定）。\n"
        "3. IPIGuard 把五格填满了，但「判定」那一格里写的是：工具 ∈ 计划图？\n"
        "4. 我们那一格换成了：工具在 T 内、对象在 O 内、每个参数值的来源，外加独立裁判。\n\n"
        "结构性变化就四条：① 新增解析器（只读用户请求 → 授权范围）；"
        "② 判定单元从工具名放大到整次调用，且判定器独立于规划器；"
        "③ 图从「计划期建好、执行期只追加只读节点」变成「每轮追加证据/委托/参数」；"
        "④ 新增输出审核。\n\n"
        "一句话收尾：我们没有把计划做大，而是把判定从计划里搬到一个独立的、执行前的组件，"
        "并为它补了两种表示——授权范围与证据来源。")

    add_figure_slide(
        prs, os.path.join(HERE, "fig6-two-gates.svg"),
        "「两边都拦、但拦法不同」（约 2 分钟）：\n"
        "1. 注入同时干两件事：加一个用户没要求的动作（删邮件）、改一个用户要求过的动作的参数（收款人改 US999）。\n"
        "2. 左线闸门在「工具」：删邮件不在计划图里 → 拦下；转账在计划图里 → 放行，参数它不管。\n"
        "3. 右线闸门在「值」：删邮件工具不在允许集 → 拦；US999 只出现在不可信正文 → 也拦。\n"
        "4. 一句话：准入检查问「这件事报备过吗」，来源检查问「这个值通向哪个根」。")

    add_figure_slide(
        prs, os.path.join(HERE, "fig7-ipiguard-trace.svg"),
        "IPIGuard 的成功路径（6 步）：\n"
        "1. 一次规划出整张图（n1 查交易 → n2 转账）。\n"
        "2. 按拓扑序执行；只放行图里的工具，另允许只读扩展。\n"
        "3. 注入要求“转发账单邮件”——不在图里、且是写操作 → 根本进不去。\n"
        "4. 转账按计划执行，任务完成。\n\n"
        "讲的时候要点出来：它挡的是「计划外的新动作」，所以这一类它几乎必拦。")

    add_figure_slide(
        prs, os.path.join(HERE, "fig8-eag-trace.svg"),
        "我们的 12 步（同一个任务）：\n"
        "分段讲：1-4 解析与读取；5-6 切片与建图；7-9 判定；10-12 恢复与出口。\n\n"
        "最关键的一句：12 步里只有第 8、9 步是「判定」，其余都是让判定能成立的基础设施——"
        "解析定基准、切片出字段、建图连来源、核对防替换、审核管出口。\n"
        "被问「为什么这么重」时，就指这 12 步：少任何一步，判定都会退化成比字符串。")

    add_figure_slide(
        prs, os.path.join(HERE, "fig5-task-walkthrough.svg"),
        "「漏过的那一条，后果有多大」（约 2 分钟）：\n"
        "1. 上半是共同部分：同一份被改过的账单、同一个模型、同一个错误提议（9999）。\n"
        "2. 分叉之后，左线只问一句「转账在不在计划图里」→ 在 → 执行，钱转错且不可逆。\n"
        "3. 右线问「这笔金额通向哪个根」→ 只连到不可信正文 → 拒绝。\n"
        "4. 关键：拒绝不是终点。返回可操作原因（账单字段是 98.70）→ 重规划 → 放行 → 任务照样做完。\n"
        "5. 收尾：差别不是「谁更不容易被骗」，而是「被骗之后会不会真的执行」。\n\n"
        "可能被问「这是不是说 IPIGuard 一定失败」：不是。它用伪造工具调用降低模型估错的概率，"
        "本图画的正是「估错」那一支；它论文里也承认攻击成功率不精确为零，漏的就是这一支。")

    add_figure_slide(
        prs, os.path.join(HERE, "fig9-failure-case.svg"),
        "真实失败案例（建议主动放，别等人问）：\n"
        "1. 开门见山：这是我们自己实验里被穿透的一对，守卫开着，6 个动作全部放行。\n"
        "2. 轨迹是逐条从结果文件里取的，不是编的。\n"
        "3. 根因：授权绑了「值」，没绑「角色」——同一个账号在付房租里合法，在退款给朋友里就越权。\n"
        "4. 补法：把授权从「值白名单」升级成「工具 + 子任务目的 + 对象角色」。\n\n"
        "这段讲好了是加分项：它说明我们清楚自己的边界在哪，而不是只会报 0.64%。")

    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "EAG-Guard-配图.pptx")
    prs.save(out)
    print("saved:", out, os.path.getsize(out), "bytes")
    print("slides:", len(prs.slides))


if __name__ == "__main__":
    main()
