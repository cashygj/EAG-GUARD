# -*- coding: utf-8 -*-
"""交互图（两页）：
图1 AgentDojo 与智能体的交互
图2 AgentDojo 的功能模块 + 与 Qwen 的交互 + 守卫（新增）
黑白、原生形状、可编辑。
"""
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

TITLE_PT = 20
BOX_TITLE_PT = 13
BOX_LINE_PT = 10.5
LABEL_PT = 9.5
CAPTION_PT = 10


def _set_font(run, size, bold=False, font=SONG):
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


def box(slide, x, y, w, h, title, lines=(), thick=False, dashed=False, title_only=False):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = WHITE
    s.line.color.rgb = BLACK
    s.line.width = Pt(2.25 if thick else 1.0)
    if dashed:
        s.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    s.shadow.inherit = False
    tf = s.text_frame
    tf.word_wrap = True
    s.text_frame.margin_left = Inches(0.06)
    s.text_frame.margin_right = Inches(0.06)
    s.text_frame.margin_top = Inches(0.03)
    s.text_frame.margin_bottom = Inches(0.03)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = title
    _set_font(r, BOX_TITLE_PT, True, HEI)
    for ln in lines:
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run()
        r2.text = ln
        _set_font(r2, BOX_LINE_PT, False, SONG)
    return s


def textbox(slide, x, y, w, h, text, size=LABEL_PT, bold=False, font=SONG,
            align=PP_ALIGN.CENTER, fill=False):
    t = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if fill:
        t.fill.solid()
        t.fill.fore_color.rgb = WHITE
        t.line.fill.background()
    tf = t.text_frame
    tf.word_wrap = False
    for a in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, a, 0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    _set_font(r, size, bold, font)
    return t


def arrow(slide, x1, y1, x2, y2, label=None, lx=None, ly=None, lw=0.95,
          dash=False, both=False, size=LABEL_PT, label_fill=True):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                                   Inches(x2), Inches(y2))
    c.line.color.rgb = BLACK
    c.line.width = Pt(1.0)
    if dash:
        c.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    ln = c.line._get_or_add_ln()
    ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    if both:
        ln.append(ln.makeelement(qn("a:headEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    if label:
        textbox(slide, lx, ly, lw, 0.24, label, size=size, fill=label_fill)


def caption(slide, lines, y=6.5, size=CAPTION_PT):
    t = slide.shapes.add_textbox(Inches(0.6), Inches(y), Inches(12.1), Inches(0.9))
    tf = t.text_frame
    tf.word_wrap = True
    for a in ("margin_left", "margin_top", "margin_bottom"):
        setattr(tf, a, 0)
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run()
        r.text = ln
        _set_font(r, size, False, SONG)


def title(slide, text, y=0.26, size=TITLE_PT):
    textbox(slide, 0.6, y, 12.1, 0.46, text, size=size, bold=True, font=HEI)


prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]

# ============================================================ 图1
s1 = prs.slides.add_slide(blank)
title(s1, "图1　AgentDojo 与智能体的交互")

box(s1, 1.1, 1.55, 4.6, 3.0, "AgentDojo（评测基准）", [
    "环境状态（账单 / 邮件 / 余额…）",
    "工具库（74 个工具）",
    "用户任务 + 校验函数",
    "注入任务 + 注入点",
    "评分：utility / security",
])
box(s1, 7.6, 1.55, 4.6, 3.0, "智能体（ReAct 循环）", [
    "系统提示 + 用户任务",
    "大模型（Qwen3.5-27B）",
    "工具执行器",
    "循环控制（最多 15 轮）",
])

arrow(s1, 5.75, 2.1, 7.55, 2.1, "① 任务提示", 5.95, 1.80, 1.25)
arrow(s1, 7.55, 2.95, 5.75, 2.95, "② 工具调用", 5.95, 2.66, 1.25)
arrow(s1, 5.75, 3.80, 7.55, 3.80, "③ 结果回填", 5.95, 3.51, 1.25)

caption(s1, ["说明：智能体是 AgentDojo 自带的 ReAct 实现，模型由实验指定；工具调用直接读写环境状态。",
             "评分在评测层完成——用校验函数比对执行前后的环境状态，与智能体无关。"])

# ============================================================ 图2
s2 = prs.slides.add_slide(blank)
title(s2, "图2　AgentDojo 的功能模块与同 Qwen 的交互")

W, H = 2.0, 1.2
ys = 3.05
xs = [0.3, 3.0, 5.7, 8.4, 11.1]

# 上排
box(s2, xs[1], 1.45, W, 1.0, "任务层", ["任务 + 校验函数", "注入任务"])
box(s2, xs[4], 1.45, W, 1.0, "攻击层", ["写入注入点", "629 个用例"])
# 中排（链条）
box(s2, xs[0], ys, W, H, "Qwen3.5-27B", ["外部大模型", "只生成调用"])
box(s2, xs[1], ys, W, H, "运行时（循环）", ["AgentDojo 内置", "发请求、收调用", "最多 15 轮"])
box(s2, xs[2], ys, W, H, "守卫（本方法新增）", ["判定后才执行"], thick=True, dashed=True)
box(s2, xs[3], ys, W, H, "工具层", ["74 个工具函数"])
box(s2, xs[4], ys, W, H, "数据层", ["环境状态", "注入点"])
# 下排
box(s2, xs[4], 4.85, W, 1.0, "评测层", ["utility / security", "（校验函数来自任务层）"])

# 运行链
arrow(s2, xs[1], 3.35, xs[0] + W, 3.35, "① 上下文", xs[0] + W + 0.05, 3.10, 0.75)
arrow(s2, xs[0] + W, 3.90, xs[1], 3.90, "② tool_calls", xs[0] + W + 0.02, 3.94, 0.85)
arrow(s2, xs[1] + W, 3.65, xs[2], 3.65, "③ 请求", xs[1] + W + 0.03, 3.40, 0.7, both=True)
arrow(s2, xs[2] + W, 3.65, xs[3], 3.65, "④ 放行执行", xs[2] + W + 0.02, 3.40, 0.85)
arrow(s2, xs[3] + W, 3.65, xs[4], 3.65, "⑤ 读写", xs[3] + W + 0.03, 3.40, 0.7)

# 上下连线
arrow(s2, xs[1] + W / 2, 2.45, xs[1] + W / 2, ys, "任务提示", xs[1] + W / 2 + 0.05, 2.62, 0.85)
arrow(s2, xs[4] + W / 2, 2.45, xs[4] + W / 2, ys, "注入", xs[4] + W / 2 + 0.05, 2.62, 0.6)
arrow(s2, xs[4] + W / 2, ys + H, xs[4] + W / 2, 4.85, "状态快照", xs[4] + W / 2 + 0.05, 4.42, 0.95, dash=True)

caption(s2, [
    "说明：实线框为 AgentDojo 的功能模块；粗虚线框为本方法新增的守卫，插在“运行时”与“工具层”之间；"
    "最左侧 Qwen 为外部大模型，只负责生成工具调用，不接触环境。",
    "运行期（实线）：运行时把上下文送给 Qwen → Qwen 返回 tool_calls → 守卫判定 → 通过后由工具层执行并改写数据层 → "
    "结果回填，进入下一轮。判分期（虚线）：数据层把执行前后的状态快照交给评测层打分，任务层提供校验函数。",
], y=6.35)

# ============================================================ 图3 结构图（对齐导师排版）
def node(slide, x, y, w, h, text, shape=MSO_SHAPE.RECTANGLE, size=8.5, bold=False):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = WHITE
    s.line.color.rgb = BLACK
    s.line.width = Pt(1.0)
    s.shadow.inherit = False
    tf = s.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.03)
    tf.margin_right = Inches(0.03)
    tf.margin_top = Inches(0.01)
    tf.margin_bottom = Inches(0.01)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    _set_font(r, size, bold, SONG)
    return s


s3 = prs.slides.add_slide(blank)
title(s3, "图3　EAG-Guard 在 AgentDojo 中的位置", y=0.10, size=18)

# ---------- 右：AgentDojo 大框 ----------
box(s3, 7.00, 0.55, 6.15, 6.80, "", thick=True)
textbox(s3, 7.16, 0.60, 5.0, 0.22, "AgentDojo 0.1.35（评测基准）", size=9, align=PP_ALIGN.LEFT)

node(s3, 7.35, 0.90, 4.30, 0.72, "Task Suite 任务集\nUserTask 正常任务 · InjectionTask 注入任务 · 交叉 629 用例", size=8)

box(s3, 7.35, 1.80, 4.30, 1.92, "", dashed=True)
textbox(s3, 7.45, 1.82, 2.0, 0.18, "ENV 环境", size=8, align=PP_ALIGN.LEFT)
for i, name in enumerate(["workspace 邮件 / 文件 / 日历", "banking 网银转账",
                          "travel 预订酒店", "slack 企业消息"]):
    node(s3, 7.60, 2.04 + i * 0.40, 3.80, 0.34, name, size=8)

node(s3, 7.35, 3.86, 4.30, 0.60, "Env State 环境状态机（保存数据、埋入注入载荷）", size=8.5)

node(s3, 8.60, 4.82, 2.75, 0.62, "Judge 结果判定器\nutility · security", size=8)
node(s3, 8.60, 5.62, 2.75, 0.50, "Trace Logger 交互轨迹", size=8)
node(s3, 8.90, 6.42, 2.45, 0.62, "Tool Runtime 工具执行引擎\n执行动作、变更状态", size=8)

# ---------- 中间：守卫（本方法） ----------
box(s3, 4.10, 4.60, 2.80, 1.90, "", thick=True, dashed=True)
textbox(s3, 4.20, 4.63, 2.50, 0.20, "EAG-Guard 守卫（本方法新增）", size=8.5, align=PP_ALIGN.LEFT)
for i, txt in enumerate(["① 工具与对象在授权范围内？",
                         "② 参数值可溯源到可信根？",
                         "③ 语义裁判通过？",
                         "④ 签名一致？"]):
    node(s3, 4.22, 4.86 + i * 0.28, 2.56, 0.24, txt, size=7.5)
node(s3, 4.22, 6.06, 2.56, 0.24, "全部通过才执行；否则只回理由", size=7)

# ---------- 左下：被测智能体 ----------
box(s3, 0.35, 4.20, 2.55, 2.30, "", thick=True)
textbox(s3, 0.44, 4.24, 2.40, 0.22, "被测智能体（外部）", size=9, align=PP_ALIGN.LEFT)
node(s3, 0.45, 4.52, 2.35, 0.52, "Qwen3.5-27B（只提议，不执行）", size=8)
node(s3, 0.45, 5.14, 2.35, 0.46, "循环控制（最多 15 轮）", size=8)
node(s3, 0.45, 5.70, 2.35, 0.46, "上下文组装 / 结果回填", size=8)

# ---------- 箭头 ----------
arrow(s3, 9.50, 1.62, 9.50, 1.80, None)
arrow(s3, 9.50, 3.72, 9.50, 3.86, None)

arrow(s3, 7.35, 4.16, 2.90, 4.16, "不可信返回（含注入载荷）", 4.55, 3.90, 2.4)

arrow(s3, 2.90, 4.98, 4.10, 4.98, None)
textbox(s3, 2.95, 4.72, 1.10, 0.20, "tool_call（仅提议）", size=7.5, align=PP_ALIGN.LEFT)

arrow(s3, 4.10, 5.52, 2.90, 5.52, None)
textbox(s3, 2.95, 5.56, 1.10, 0.20, "拒绝·附理由", size=7.5, align=PP_ALIGN.LEFT)

arrow(s3, 6.90, 6.05, 8.90, 6.70, None)
textbox(s3, 5.80, 6.64, 1.05, 0.20, "通过才执行", size=7.5, align=PP_ALIGN.RIGHT)

arrow(s3, 9.97, 4.46, 9.97, 4.82, None)
arrow(s3, 9.97, 5.44, 9.97, 5.62, None)

# 变更状态：Tool Runtime → Env State（贴右边）
arrow(s3, 11.35, 6.73, 12.55, 6.73, None)
arrow(s3, 12.55, 6.73, 12.55, 4.16, None)
arrow(s3, 12.55, 4.16, 11.65, 4.16, None)
textbox(s3, 12.60, 5.05, 0.50, 0.90, "变\n更\n状\n态", size=7.5, align=PP_ALIGN.LEFT)

# ---------- 创新点说明 ----------
textbox(s3, 0.40, 0.90, 3.55, 2.90,
        "创新点：\n"
        "① 位置：判定放在“模型提议”与\n"
        "　“工具执行”之间，既不是输入\n"
        "　过滤，也不是事后审计；\n"
        "② 粒度：判的是“参数值从哪来”\n"
        "　（字段级溯源），不只是工具名；\n"
        "③ 处置：拒绝时不执行，只把可\n"
        "　操作的理由回给模型重试。",
        size=8, align=PP_ALIGN.LEFT)

# ============================================================ 图4 时序图
s4 = prs.slides.add_slide(blank)
title(s4, "图4　EAG-Guard 的调用时序（守卫位于“提议”与“执行”之间）", y=0.10, size=16)

LANES = [("用户", 1.30), ("AgentDojo", 3.70), ("Qwen3.5-27B", 6.45),
         ("守卫（本方法）", 9.15), ("工具执行器", 11.85)]
TOP, BOT = 0.72, 6.30

for name, lx in LANES:
    thick = name.startswith("守卫")
    node(s4, lx - 1.00, TOP, 2.00, 0.48, name, MSO_SHAPE.RECTANGLE, 9.5, thick)
    node(s4, lx - 1.00, BOT, 2.00, 0.42, name, MSO_SHAPE.RECTANGLE, 9)
    c = s4.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(lx), Inches(TOP + 0.48),
                                Inches(lx), Inches(BOT))
    c.line.color.rgb = BLACK
    c.line.width = Pt(0.75)
    c.line.dash_style = MSO_LINE_DASH_STYLE.DASH

XU, XA, XQ, XG, XT = (lx for _, lx in LANES)


def msg(y, x1, x2, text, dash=False):
    c = s4.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y),
                                Inches(x2), Inches(y))
    c.line.color.rgb = BLACK
    c.line.width = Pt(1.0)
    if dash:
        c.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    ln = c.line._get_or_add_ln()
    ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    left, right = min(x1, x2), max(x1, x2)
    textbox(s4, left + 0.05, y - 0.24, max(right - left - 0.10, 1.0), 0.22,
            text, size=8.5, fill=True)


def selfloop(y, lx, text, side="right"):
    c1 = s4.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(lx), Inches(y),
                                 Inches(lx + 0.55), Inches(y))
    c2 = s4.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(lx + 0.55), Inches(y),
                                 Inches(lx + 0.55), Inches(y + 0.26))
    c1.line.color.rgb = c2.line.color.rgb = BLACK
    c1.line.width = c2.line.width = Pt(1.0)
    c3 = s4.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(lx + 0.55), Inches(y + 0.26),
                                 Inches(lx), Inches(y + 0.26))
    c3.line.color.rgb = BLACK
    c3.line.width = Pt(1.0)
    ln3 = c3.line._get_or_add_ln()
    ln3.append(ln3.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    if side == "right":
        textbox(s4, lx + 0.65, y - 0.02, 3.0, 0.24, text, size=8, align=PP_ALIGN.LEFT, fill=True)
    else:
        textbox(s4, lx - 3.0, y - 0.02, 2.42, 0.24, text, size=8, align=PP_ALIGN.RIGHT, fill=True)


msg(1.50, XU, XA, "① 下发目标任务")
msg(1.94, XA, XQ, "② 返回带注入载荷的上下文")
msg(2.38, XQ, XG, "③ 输出 tool_call（仅提议，未执行）")
selfloop(2.82, XG, "④ 判定：T/O、字段级溯源、裁判、签名", side="right")
msg(3.42, XG, XQ, "⑤ 拒绝·附理由（不执行）", dash=True)
msg(3.86, XG, XT, "⑥ 通过才执行")
msg(4.30, XT, XA, "⑦ 执行动作、变更环境状态")
msg(4.74, XA, XQ, "⑧ 新一轮上下文（循环直到任务结束）", dash=True)
msg(5.18, XG, XA, "⑨ 审核后的最终回答")
msg(5.62, XA, XU, "⑩ 返回给用户")
selfloop(5.92, XA, "⑪ 比对前后状态，生成评测报告", side="right")

textbox(s4, 0.55, 6.95, 12.2, 0.26,
        "要点：守卫不改写模型看到的上下文；它只在每个 tool_call 真正执行之前判定一次——"
        "拒绝时不执行，只把可操作的理由回给模型。",
        size=9, align=PP_ALIGN.LEFT)

out = os.path.join(HERE, "AgentDojo-交互图.pptx")
prs.save(out)
print("saved:", out, os.path.getsize(out), "bytes")
