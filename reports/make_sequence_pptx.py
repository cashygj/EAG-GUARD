# -*- coding: utf-8 -*-
"""EAG-Guard 时序图：用户 / AgentDojo / 守卫 / 模型。黑白、原生形状、可编辑。"""
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
BLACK = RGBColor(0, 0, 0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SONG = "宋体"
HEI = "黑体"


def _font(run, size, bold=False, font=SONG):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = BLACK
    run.font.name = "Times New Roman"
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", font)


def textbox(slide, x, y, w, h, text, size=9.5, bold=False, font=SONG, align=PP_ALIGN.CENTER, fill=False):
    t = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if fill:
        t.fill.solid()
        t.fill.fore_color.rgb = WHITE
        t.line.fill.background()
    tf = t.text_frame
    tf.word_wrap = False
    for attr in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, attr, 0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    _font(r, size, bold, font)
    return t


def rect(slide, x, y, w, h, text, size=11, thick=False):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = WHITE
    s.line.color.rgb = BLACK
    s.line.width = Pt(1.75 if thick else 1.0)
    s.shadow.inherit = False
    tf = s.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.02)
    tf.margin_right = Inches(0.02)
    tf.margin_top = Inches(0.01)
    tf.margin_bottom = Inches(0.01)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    _font(r, size, True, HEI)
    return s


def line(slide, x1, y1, x2, y2, arrow=True, dash=False, head=False):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                                   Inches(x2), Inches(y2))
    c.line.color.rgb = BLACK
    c.line.width = Pt(1.0)
    if dash:
        c.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    ln = c.line._get_or_add_ln()
    if arrow:
        ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    if head:
        ln.append(ln.makeelement(qn("a:headEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    return c


def message(slide, x1, x2, y, text, both=False):
    line(slide, x1, y, x2, y, head=both)
    left, right = min(x1, x2), max(x1, x2)
    textbox(slide, left + 0.06, y - 0.245, max(right - left - 0.12, 0.6), 0.22, text, fill=True)


def self_loop(slide, x, y, text, width=0.42, height=0.2):
    """自调用：右侧一个小方框形回环。"""
    line(slide, x, y, x + width, y, arrow=False)
    line(slide, x + width, y, x + width, y + height, arrow=False)
    line(slide, x + width, y + height, x, y + height, arrow=True)
    textbox(slide, x + width + 0.08, y - 0.04, 2.6, 0.24, text, align=PP_ALIGN.LEFT)


prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
s = prs.slides.add_slide(prs.slide_layouts[6])

textbox(s, 0.6, 0.22, 12.1, 0.42, "EAG-Guard 的调用时序（守卫位于“提议”与“执行”之间）",
        size=17, bold=True, font=HEI)

# 角色与生命线
actors = [("用户", 1.55), ("AgentDojo", 4.45), ("守卫（EAG-Guard）", 7.55), ("大模型", 10.75)]
TOP = 0.85
BOT = 6.45
for name, x in actors:
    rect(s, x - 1.0, TOP, 2.0, 0.5, name, thick=(name.startswith("守卫")))
    rect(s, x - 1.0, BOT, 2.0, 0.45, name, size=10)
    line(s, x, TOP + 0.5, x, BOT, arrow=False, dash=True)

# 阶段标记
textbox(s, 0.15, 1.48, 1.15, 0.25, "准备（一次）", size=9, align=PP_ALIGN.LEFT)
textbox(s, 0.15, 2.95, 1.15, 0.25, "执行循环（每轮）", size=9, align=PP_ALIGN.LEFT)
textbox(s, 0.15, 5.78, 1.15, 0.25, "结束", size=9, align=PP_ALIGN.LEFT)

X_USER, X_SUITE, X_GUARD, X_MODEL = (x for _, x in actors)

# 准备
message(s, X_USER, X_SUITE, 1.70, "① 下发目标任务")
message(s, X_SUITE, X_GUARD, 2.10, "② 任务提示 + 工具清单")
message(s, X_GUARD, X_MODEL, 2.42, "③ 请求解析授权范围（一次）")   # 双向示意
message(s, X_MODEL, X_GUARD, 2.74, "返回 T/O/P")

# 循环
message(s, X_SUITE, X_MODEL, 3.20, "④ 送入上下文")
line(s, X_MODEL, 3.60, X_GUARD, 3.60)
textbox(s, X_GUARD - 1.55, 3.335, 4.75, 0.24,
        "⑤ tool_call：已由框架解析为工具名 + 参数（仅提议，未执行）",
        align=PP_ALIGN.LEFT, fill=True)
self_loop(s, X_GUARD, 3.85, "⑥ 判定：T/O、参数来源、裁判、签名")
message(s, X_GUARD, X_SUITE, 4.45, "⑦ 通过才执行；拒绝则附理由回模型")
self_loop(s, X_SUITE, 4.75, "⑧ 执行工具、更新环境状态")
message(s, X_SUITE, X_GUARD, 5.35, "⑨ 结果回填 → 切片入图")

# 结束
message(s, X_GUARD, X_USER, 5.95, "⑩ 输出审核后的最终回答")
self_loop(s, X_SUITE, 6.10, "⑪ 评测：utility / security", width=0.36)

textbox(s, 0.6, 7.02, 12.1, 0.34,
        "要点：守卫不修改模型看到的上下文；它只在每个 tool_call 真正执行之前做一次判定。",
        size=10, align=PP_ALIGN.LEFT)

out = os.path.join(HERE, "EAG-Guard-时序图.pptx")
prs.save(out)
print("saved:", out, os.path.getsize(out), "bytes")
