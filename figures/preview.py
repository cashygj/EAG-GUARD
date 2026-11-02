# -*- coding: utf-8 -*-
"""把本仓库生成的 SVG 栅格化成 PNG，用于版式自检（仅供预览）。

只支持本图用到的子集：rect / line / path(M,L) / polygon / circle / text。
不处理 dash、opacity（预览足够）。
"""
import re
import sys
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

NS = "{http://www.w3.org/2000/svg}"
FONT_DIR = r"C:\Windows\Fonts"
REG = FONT_DIR + r"\msyh.ttc"
BOLD = FONT_DIR + r"\msyhbd.ttc"
MONO = FONT_DIR + r"\consola.ttf"
MONO_B = FONT_DIR + r"\consolab.ttf"

_cache = {}


def font(family, size, weight):
    mono = family and "Consolas" in family
    if mono:
        path = MONO_B if weight == "bold" else MONO
    else:
        path = BOLD if weight == "bold" else REG
    key = (path, int(round(size)))
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, int(round(size)))
    return _cache[key]


def color(v, default=None):
    if not v or v == "none":
        return default
    if v.startswith("#"):
        v = v[1:]
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def draw_path(d, draw, stroke, width, scale=1.0):
    toks = re.findall(r"[ML]\s*([-\d.]+)[ ,]([-\d.]+)", d)
    pts = [(float(a) * scale, float(b) * scale) for a, b in toks]
    if len(pts) >= 2:
        draw.line(pts, fill=stroke, width=max(1, int(round(width))), joint="curve")


def main(src, dst, scale=1.0):
    tree = ET.parse(src)
    root = tree.getroot()
    W = int(num(root.get("width")))
    H = int(num(root.get("height")))
    img = Image.new("RGB", (int(W * scale), int(H * scale)), "white")
    d = ImageDraw.Draw(img)

    for el in root.iter():
        tag = el.tag.replace(NS, "")
        if tag == "rect":
            x, y = num(el.get("x")), num(el.get("y"))
            w, h = num(el.get("width")), num(el.get("height"))
            rx = num(el.get("rx"))
            fill = color(el.get("fill"))
            stroke = color(el.get("stroke"))
            sw = num(el.get("stroke-width"), 1)
            box = [x * scale, y * scale, (x + w) * scale, (y + h) * scale]
            if rx > 0:
                if fill and stroke:
                    d.rounded_rectangle(box, radius=rx * scale, fill=fill,
                                        outline=stroke, width=max(1, int(round(sw))))
                elif fill:
                    d.rounded_rectangle(box, radius=rx * scale, fill=fill)
                elif stroke:
                    d.rounded_rectangle(box, radius=rx * scale, outline=stroke,
                                        width=max(1, int(round(sw))))
            else:
                d.rectangle(box, fill=fill, outline=stroke,
                            width=max(1, int(round(sw))) if stroke else 0)
        elif tag == "line":
            d.line([(num(el.get("x1")) * scale, num(el.get("y1")) * scale),
                    (num(el.get("x2")) * scale, num(el.get("y2")) * scale)],
                   fill=color(el.get("stroke"), (0, 0, 0)),
                   width=max(1, int(round(num(el.get("stroke-width"), 1)))))
        elif tag == "path":
            draw_path(el.get("d"), d, color(el.get("stroke"), (0, 0, 0)),
                      num(el.get("stroke-width"), 1) * scale, scale)
        elif tag == "polygon":
            raw = re.findall(r"([-\d.]+),([-\d.]+)", el.get("points"))
            pts = [(float(a) * scale, float(b) * scale) for a, b in raw]
            if len(pts) >= 3:
                d.polygon(pts, fill=color(el.get("fill")))
        elif tag == "circle":
            cx, cy, r = num(el.get("cx")), num(el.get("cy")), num(el.get("r"))
            d.ellipse([(cx - r) * scale, (cy - r) * scale,
                       (cx + r) * scale, (cy + r) * scale],
                      fill=color(el.get("fill")))
        elif tag == "text":
            s = el.text or ""
            if not s.strip():
                continue
            x, y = num(el.get("x")), num(el.get("y"))
            size = num(el.get("font-size"), 12)
            f = font(el.get("font-family") or "", size * scale,
                     el.get("font-weight") or "normal")
            anchor = el.get("text-anchor") or "start"
            fill = color(el.get("fill"), (0, 0, 0))
            wpx = d.textlength(s, font=f)
            if anchor == "middle":
                px = x * scale - wpx / 2
            elif anchor == "end":
                px = x * scale - wpx
            else:
                px = x * scale
            d.text((px, y * scale), s, font=f, fill=fill, anchor="ls")

    img.save(dst)
    print("preview:", dst, img.size)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 1.0)
