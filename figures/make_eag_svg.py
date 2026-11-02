# -*- coding: utf-8 -*-
"""生成两张讲解图（SVG，PowerPoint 可编辑），标注全中文：

  fig1-eag-nodes-edges.svg  —— 六类节点 + 五类边连成一张拓扑图（1280x740）
  fig2-eag-instance-fpr.svg —— 一张实例 + 字段级溯源判定（1600x800）

术语对应（图里只用中文）：
  证据—授权—动作图 = EAG；字段级溯源可达性 = FPR
  grants=授予  delegates=声明委托  supports=支撑  derives=派生  produces=产出
  user-delegated=用户委托  injected=注入  untrusted=不可信

PowerPoint 兼容约束：只用 rect/path/polygon/line/circle/text；不用 style 块、
filter、marker、clipPath、use、image；箭头尖是独立 polygon；文字逐行独立且一律
左对齐（不依赖 text-anchor）；按语义分组（<g id=...>）。
"""
import math
import os

FONT = "Microsoft YaHei, PingFang SC, Segoe UI, sans-serif"

NAVY = "#16283F"
INK = "#243447"
INK2 = "#4A5A6A"
MUTED = "#71808F"

BLUE = "#2F5597"
BLUE_L = "#EAF0F8"
AMBER = "#A9761A"
AMBER_L = "#FBF3E2"
TEAL = "#0F766E"
TEAL_L = "#E6F2F0"
GREEN = "#2E7D32"
GREEN_L = "#EAF3EA"
RED = "#C0392B"
RED_L = "#FBEBE8"
GRAY = "#5B6B7C"
GRAY_L = "#F1F4F7"

out = []
W = H = 0


def reset(w, h):
    global out, W, H
    out, W, H = [], w, h
    out.append(f'<rect x="0" y="0" width="{w}" height="{h}" fill="#FFFFFF"/>')


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def w_of(s, size):
    return sum(size if ord(c) > 0x2E7F else size * 0.56 for c in s)


def text(x, y, s, size=12.5, fill=INK, weight="normal"):
    if not s:
        return
    out.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
               f'fill="{fill}" font-weight="{weight}">{esc(s)}</text>')


def rect(x, y, w, h, fill, stroke="none", rx=10, sw=1.4):
    out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
               f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def line(x1, y1, x2, y2, color, w=1.6, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
               f'stroke="{color}" stroke-width="{w}" stroke-linecap="round"{d}/>')


def arrow(pts, color, w=2.2, dash=None, head=10.0):
    pts = [(float(a), float(b)) for a, b in pts]
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    n = math.hypot(dx, dy) or 1.0
    ux, uy = dx / n, dy / n
    ex, ey = x2 - ux * head * 0.82, y2 - uy * head * 0.82
    d = f' stroke-dasharray="{dash}"' if dash else ""
    path = " ".join(f"{'M' if i == 0 else 'L'}{a:.1f},{b:.1f}"
                    for i, (a, b) in enumerate(pts[:-1]))
    path += f" L{ex:.1f},{ey:.1f}"
    out.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{w}" '
               f'stroke-linejoin="round" stroke-linecap="round"{d}/>')
    px, py = -uy, ux
    p2 = (x2 - ux * head + px * head * 0.44, y2 - uy * head + py * head * 0.44)
    p3 = (x2 - ux * head - px * head * 0.44, y2 - uy * head - py * head * 0.44)
    out.append(f'<polygon points="{x2:.1f},{y2:.1f} {p2[0]:.1f},{p2[1]:.1f} '
               f'{p3[0]:.1f},{p3[1]:.1f}" fill="{color}"/>')


def label(x, y, s, color=INK2, size=11.5, anchor="start", pad=4, bold=False):
    w = w_of(s, size)
    x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
    rect(x0 - pad, y - size + 1, w + pad * 2, size + 6, "#FFFFFF", "none", rx=3, sw=0)
    text(x0, y, s, size, color, "bold" if bold else "normal")


def ctext(cx, y, s, size=10, fill=MUTED, weight="normal"):
    text(cx - w_of(s, size) / 2, y, s, size, fill, weight)


def node(x, y, w, h, color, tint, title, lines, tag=None, tag_color=None,
         title_size=14.5, line_size=12.2):
    rect(x, y, w, h, tint, color, rx=12, sw=1.8)
    out.append(f'<rect x="{x}" y="{y}" width="6" height="{h}" rx="3" fill="{color}"/>')
    text(x + 18, y + 26, title, title_size, color, "bold")
    for i, ln in enumerate(lines):
        text(x + 18, y + 47 + i * 19, ln, line_size, INK)
    if tag:
        tw = w_of(tag, 10.5) + 14
        tx = x + w - tw - 10
        rect(tx, y + 8, tw, 18, tag_color or color, "none", rx=9, sw=0)
        text(tx + 7, y + 21, tag, 10.5, "#FFFFFF", "bold")


def pill(x, y, w, h, color, tint, title, sub=None):
    rect(x, y, w, h, tint, color, rx=8, sw=1.3)
    text(x + 10, y + (h / 2 + 4 if not sub else 14), title, 11.2, color, "bold")
    if sub:
        text(x + 10, y + 27, sub, 10.2, INK2)


def group(name):
    out.append(f'<g id="{name}">')


def endgroup():
    out.append("</g>")


def svg_bytes():
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" version="1.1">\n' + "\n".join(out) + "\n</svg>\n")


# ======================================================================
# 图 1：六类节点 + 五类边，连在同一张图上
# ======================================================================
def build_types():
    reset(1280, 740)

    group("title")
    text(48, 56, "证据—授权—动作图：六类节点与五类边怎么连", 26, NAVY, "bold")
    text(48, 86, "授权只从用户请求推导；证据来自工具返回；参数是动作的实参——五类边把它们连成一张可回溯的图。",
         12.8, INK2)
    line(48, 102, W - 48, 102, "#D8E0E8", 1.2)
    endgroup()

    # ---------------- 节点 ----------------
    group("nodes")
    node(60, 104, 200, 88, BLUE, BLUE_L, "用户请求",
         ["唯一可信输入", "解析器不读工具返回"], tag="可信根", tag_color=BLUE,
         title_size=13.5, line_size=11.8)

    node(500, 98, 250, 100, AMBER, AMBER_L, "授权范围",
         ["工具 / 对象 / 参数来源", "由用户请求经「授予」推导"], line_size=12)

    # 授权范围的两个成员：工具 / 对象（判定前单独查，不是图上的边）
    for i, nm in enumerate(["工具", "对象"]):
        py = 110 + i * 36
        pill(772, py, 88, 28, BLUE, BLUE_L, nm)
        line(750, py + 14, 772, py + 14, BLUE, 1.3, "3,3")

    node(500, 292, 240, 100, TEAL, TEAL_L, "参数",
         ["每个实参一个节点", "参数名＝取值，附来源"], title_size=14)
    node(120, 292, 240, 100, BLUE, BLUE_L, "委托",
         ["字段 ← 来源", "字段型 / 内容型"], tag="可信根", tag_color=BLUE,
         title_size=14)
    node(900, 292, 230, 100, GREEN, GREEN_L, "动作",
         ["工具（实参）签名", "规划器提议的动作"], title_size=14)
    node(500, 472, 240, 100, GRAY, GRAY_L, "证据",
         ["工具返回切片", "来源 + 可信标记 + 字段"], title_size=14)
    endgroup()

    # ---------------- 边 ----------------
    group("edges")
    arrow([(260, 148), (500, 148)], BLUE, 2.4)
    label(380, 140, "授予", BLUE, 12, "middle", bold=True)
    ctext(380, 162, "授权只由用户请求推导", 10, MUTED)

    arrow([(160, 192), (160, 292)], BLUE, 2.4)
    label(172, 248, "声明委托", BLUE, 12, bold=True)
    text(172, 266, "用户指定某字段由该来源取值", 10, MUTED)

    arrow([(360, 342), (500, 342)], GREEN, 2.8)
    label(430, 333, "派生", GREEN, 12, "middle", bold=True)
    ctext(430, 359, "运行时派生取值", 10, MUTED)

    arrow([(625, 198), (625, 292)], TEAL, 2.4)
    label(637, 250, "支撑", TEAL, 12, bold=True)
    text(637, 270, "值须落在参数来源约束内", 10, MUTED)

    arrow([(900, 342), (740, 342)], TEAL, 2.4)
    label(820, 333, "支撑", TEAL, 12, "middle", bold=True)
    ctext(820, 359, "动作挂出的实参", 10, MUTED)

    arrow([(620, 472), (620, 392)], RED, 2.6)
    label(632, 412, "支撑", RED, 12, bold=True)

    arrow([(1015, 392), (1015, 522), (740, 522)], GRAY, 2.0, dash="7,5")
    label(1027, 464, "产出", GRAY, 12, bold=True)
    endgroup()

    # ---------------- 边上的语义注解 ----------------
    group("notes")
    text(632, 432, "只由不可信证据支撑", 10.5, RED)
    text(632, 448, "→ 该值为「注入」", 10.5, RED)
    text(1027, 484, "结果切片成新证据", 10.5, MUTED)
    text(772, 192, "授权范围的成员（工具 / 对象）", 10.2, MUTED)
    endgroup()

    # ---------------- 图例 ----------------
    group("legend")
    rows = [
        [(BLUE, "授予 / 声明委托：结构边，溯源的终止根", "solid"),
         (GREEN, "派生：由委托派生 → 用户委托", "solid"),
         (TEAL, "支撑：授权或动作支撑参数", "solid")],
        [(RED, "支撑：证据支撑，来源不可信 → 注入", "solid"),
         (GRAY, "产出：动作产出新证据（不参与回溯）", "dash")],
    ]
    y = 608
    for row in rows:
        lx = 48
        for color, s, kind in row:
            if kind == "dash":
                line(lx, y, lx + 26, y, color, 2.4, "6,4")
            else:
                line(lx, y, lx + 26, y, color, 2.8)
            out.append(f'<polygon points="{lx + 33},{y} {lx + 24},{y - 4} '
                       f'{lx + 24},{y + 4}" fill="{color}"/>')
            text(lx + 40, y + 4, s, 11, INK2)
            lx += 40 + w_of(s, 11) + 34
        y += 24
    endgroup()

    # ---------------- 结论条 ----------------
    group("callout")
    rect(48, 658, W - 96, 58, "#F8FAFC", "#DCE3EA", rx=10, sw=1.1)
    text(66, 682, "字段级溯源的走法：从参数节点出发，只沿「支撑 / 派生」两类边反向回溯；到达用户请求、授权或委托"
                  "（可信根）即放行，只到达不可信证据（不可信根）即拒绝。", 12, INK)
    text(66, 703, "工具与对象是授权范围的成员，判定前先做成员检查，不参与这次回溯。", 11.5, MUTED)
    endgroup()


# ======================================================================
# 图 2：实例 + 字段级溯源判定
# ======================================================================
def build_instance():
    reset(1600, 800)

    group("title")
    text(48, 56, "一张实例：同一个工具、同一个参数位，取值来源不同，结论就不同", 27, NAVY, "bold")
    text(48, 88, "银行转账场景｜注入把金额从账单的 98.70 改成 9999｜对应流程图第 ② 步「构建图」→「独立语义审核」",
         13, INK2)
    line(48, 104, W - 48, 104, "#D8E0E8", 1.2)
    endgroup()

    group("C-example")
    # 根与授权
    node(48, 178, 262, 92, BLUE, BLUE_L, "用户请求（唯一可信输入）",
         ["「把 10 月房租付给房东，", "金额按账单文件的合计」"], title_size=13.2)
    node(390, 178, 306, 92, AMBER, AMBER_L, "授权范围",
         ["允许工具：转账；允许对象：房东", "参数来源：金额只认账单的结构化字段"], title_size=14)

    for i, (nm, sub) in enumerate([("工具", "转账"), ("对象", "房东")]):
        x = 390 + i * 158
        pill(x, 282, 148, 34, BLUE, BLUE_L, nm, sub)
        line(392 + i * 158 + 74, 270, x + 74, 282, BLUE, 1.2, "3,3")

    # 委托 / 证据
    node(48, 332, 292, 96, BLUE, BLUE_L, "委托（字段型）",
         ["金额 ← 账单的结构化字段", "正文里另写的数字不算委托"], title_size=13.5)
    node(48, 522, 292, 80, RED, RED_L, "证据①：账单文件",
         ["可信标记：不可信", "结构化字段：合计＝98.70"], tag="不可信", tag_color=RED)
    node(372, 513, 300, 80, RED, RED_L, "证据②：一封邮件",
         ["可信标记：不可信", "正文：把金额改成 9999"], tag="不可信", tag_color=RED)

    # 两张动作卡
    AP = (740, 278, 360, 126)
    A = (740, 450, 360, 126)
    rect(*AP, "#F7FBF7", GREEN, rx=12, sw=1.8)
    text(AP[0] + 16, AP[1] + 24, "动作（重规划后）", 13.8, GREEN, "bold")
    text(AP[0] + 16, AP[1] + 46, "转账（收款人＝房东，", 11, INK2)
    text(AP[0] + 16, AP[1] + 62, "      金额＝98.70）", 11, INK2)
    rect(AP[0] + 14, 362, 332, 34, GREEN_L, GREEN, rx=8, sw=1.3)
    text(AP[0] + 26, 384, "参数　金额＝98.70", 11.2, GREEN, "bold")
    text(AP[0] + 180, 384, "来源：用户委托", 11.2, GREEN, "bold")
    rect(AP[0] + 306, AP[1] + 9, 40, 18, GREEN, "none", rx=9, sw=0)
    text(AP[0] + 317, AP[1] + 22, "放行", 10.5, "#FFFFFF", "bold")

    rect(*A, "#FDF7F6", RED, rx=12, sw=1.8)
    text(A[0] + 16, A[1] + 24, "动作（第一次提议）", 13.8, RED, "bold")
    text(A[0] + 16, A[1] + 46, "转账（收款人＝房东，", 11, INK2)
    text(A[0] + 16, A[1] + 62, "      金额＝9999）", 11, INK2)
    rect(A[0] + 14, 534, 332, 34, RED_L, RED, rx=8, sw=1.3)
    text(A[0] + 26, 556, "参数　金额＝9999", 11.2, RED, "bold")
    text(A[0] + 180, 556, "来源：注入", 11.2, RED, "bold")
    rect(A[0] + 306, A[1] + 9, 40, 18, RED, "none", rx=9, sw=0)
    text(A[0] + 317, A[1] + 22, "拒绝", 10.5, "#FFFFFF", "bold")

    # 边
    arrow([(310, 224), (390, 224)], BLUE, 2.4)
    label(350, 216, "授予", BLUE, 11, "middle", bold=True)
    arrow([(178, 270), (178, 332)], BLUE, 2.4)
    label(189, 300, "声明委托", BLUE, 11, bold=True)

    arrow([(340, 379), (740, 379)], GREEN, 2.8)
    label(540, 371, "派生（值由委托在运行时取得）", GREEN, 11.5, "middle", bold=True)

    arrow([(194, 522), (194, 428)], GRAY, 1.8, dash="6,5")
    label(205, 475, "字段来源", GRAY, 11)

    arrow([(672, 551), (740, 551)], RED, 2.6)
    label(706, 541, "支撑", RED, 10.2, "middle", bold=True)

    arrow([(920, 450), (920, 404)], GRAY, 1.8, dash="6,5")
    label(920, 430, "重规划：换掉「注入」的值", GRAY, 10.8, "middle")
    endgroup()

    # ---------------- 读图说明 ----------------
    group("C-read")
    PX, PY, PW, PH = 1176, 178, 436, 422
    rect(PX, PY, PW, PH, "#F8FAFC", "#DCE3EA", rx=14, sw=1.2)
    text(PX + 20, PY + 28, "怎么读这张图", 14.5, NAVY, "bold")
    line(PX + 20, PY + 40, PX + PW - 20, PY + 40, "#DCE3EA", 1.1)
    tips = [
        (BLUE, ["蓝线「授予 / 声明委托」：由用户请求推导出的", "授权与委托，是溯源的终止根。"]),
        (GREEN, ["绿线「派生」：值取自用户委托的字段，", "来源记为「用户委托」，放行。"]),
        (RED, ["红线「支撑」：只连到不可信证据，", "来源记为「注入」，拒绝。"]),
        (GRAY, ["灰虚线：证据字段喂给委托（字段型只认", "结构化字段，正文里的数冒充不了）。"]),
        (RED, ["判定按参数：任一参数只有不可信根，", "整个动作不执行。"]),
        (GRAY, ["拒绝不是终点：返回可操作原因，换值", "重提，下一轮重新判定。"]),
    ]
    ty = PY + 68
    for color, lines in tips:
        out.append(f'<rect x="{PX + 20}" y="{ty - 9}" width="9" height="9" rx="2" fill="{color}"/>')
        for j, ln in enumerate(lines):
            text(PX + 38, ty + j * 17, ln, 11.6, INK)
        ty += 17 * len(lines) + 15
    text(PX + 20, PY + PH - 16, "用户请求与委托不在六类节点内，它们是溯源的终止根。", 11, MUTED)
    endgroup()

    # ---------------- 判定步骤 ----------------
    group("D-fpr")
    FY = 636
    text(48, FY, "字段级溯源怎么判：从参数值出发，只沿「支撑 / 派生」反向走", 15, NAVY, "bold")
    steps = [
        ("①", ["取本轮动作的每个参数节点"]),
        ("②", ["反向逐层回溯：", "只跟「支撑 / 派生」两类边"]),
        ("③", ["命中用户请求 / 授权 / 委托 → 可信根", "只命中不可信证据 → 不可信根"]),
        ("④", ["全部参数都有可信根 → 放行", "任一参数只有不可信根 → 拒绝"]),
    ]
    sw_ = [250, 386, 352, 352]
    for i, (n, lines) in enumerate(steps):
        x = 48 + sum(sw_[:i]) + i * 12
        rect(x, FY + 14, sw_[i], 62, "#FFFFFF", "#DCE3EA", rx=9, sw=1.1)
        out.append(f'<circle cx="{x + 21}" cy="{FY + 45}" r="11" fill="{TEAL}"/>')
        text(x + 16, FY + 49, n, 10.5, "#FFFFFF", "bold")
        for j, ln in enumerate(lines):
            text(x + 40, FY + 38 + j * 17, ln, 11.4, INK)
    text(48, FY + 90, "注：工具、对象两道检查不看图，直接判；溯源只回答一个问题——「这个值是从哪来的」。", 11.8, MUTED)
    endgroup()

    group("legend")
    LY = 770
    line(48, 744, W - 48, 744, "#E6EBF1", 1.0)
    items = [(BLUE, "授权 / 委托（结构边）"), (GREEN, "派生 → 放行"),
             (RED, "支撑 → 拒绝"), (GRAY, "产出 / 重规划")]
    lx = 48
    for color, s in items:
        out.append(f'<rect x="{lx}" y="{LY - 5}" width="24" height="5" rx="2.5" fill="{color}"/>')
        text(lx + 32, LY + 2, s, 11.2, INK2)
        lx += 32 + w_of(s, 11.2) + 26
    tail = "六类节点：授权 · 工具 · 对象 · 证据 · 参数 · 动作　｜　五类边：授予 · 声明委托 · 支撑 · 派生 · 产出"
    text(W - 48 - w_of(tail, 11.2), LY + 2, tail, 11.2, MUTED)
    endgroup()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    for name, fn in [("fig1-eag-nodes-edges.svg", build_types),
                     ("fig2-eag-instance-fpr.svg", build_instance)]:
        fn()
        p = os.path.join(here, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(svg_bytes())
        print("written:", name, os.path.getsize(p), "bytes", f"({W}x{H})")


if __name__ == "__main__":
    main()
