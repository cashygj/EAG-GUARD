# -*- coding: utf-8 -*-
"""把 docx 统一成规范格式（黑色字体版）：
- 所有文字纯黑，无任何彩色、无表格底色
- 正文：宋体 小四（12pt），西文 Times New Roman
- 文档标题：黑体 小三（15pt）
- 一级标题：黑体 四号（14pt）
- 二级标题：黑体 小四（12pt，加粗）
- 代码块：保留等宽（Consolas 9.5pt），同样纯黑
- 表格：文字黑色、表头加粗、字号五号（10.5pt）
"""
import sys

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

BLACK = RGBColor(0, 0, 0)
BODY_PT = 12.0      # 小四
TITLE_PT = 15.0     # 小三
H1_PT = 14.0        # 四号
CELL_PT = 10.5      # 五号
CODE_PT = 9.5

MONO = "Consolas"


def _fonts(run, east, latin):
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = rPr.makeelement(qn("w:rFonts"), {})
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), east)
    rFonts.set(qn("w:ascii"), latin)
    rFonts.set(qn("w:hAnsi"), latin)


def _style(run, size, east, latin="Times New Roman", bold=False, mono=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = BLACK
    run.font.name = latin
    _fonts(run, east, latin)


def drop_shading(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    for shd in tcPr.findall(qn("w:shd")):
        tcPr.remove(shd)


def is_mono(run):
    name = (run.font.name or "")
    return MONO.lower() in name.lower() or "courier" in name.lower()


def drop_para_shading(par):
    pPr = par._p.find(qn("w:pPr"))
    if pPr is None:
        return
    for shd in pPr.findall(qn("w:shd")):
        pPr.remove(shd)


def normalize(path):
    doc = Document(path)

    for table in doc.tables:
        for r, row in enumerate(table.rows):
            header = (r == 0)
            for cell in row.cells:
                drop_shading(cell)
                for par in cell.paragraphs:
                    for run in par.runs:
                        _style(run, CELL_PT, "宋体", bold=header)

    for i, par in enumerate(doc.paragraphs):
        drop_para_shading(par)
        centered = par.alignment is not None and int(par.alignment) == 1
        for run in par.runs:
            if not run.text.strip():
                run.font.color.rgb = BLACK
                continue

            if is_mono(run):
                _style(run, CODE_PT, "宋体", latin=MONO, mono=True)
                continue

            old = run.font.size.pt if run.font.size else BODY_PT
            bold = bool(run.font.bold)

            if bold and centered:
                _style(run, TITLE_PT, "黑体", bold=True)          # 文档标题
            elif bold and old >= 12.5:
                _style(run, H1_PT, "黑体", bold=True)             # 一级标题
            elif bold:
                _style(run, BODY_PT, "黑体", bold=True)           # 二级标题 / 强调
            else:
                _style(run, BODY_PT, "宋体")

    doc.save(path)
    return path


if __name__ == "__main__":
    for p in sys.argv[1:]:
        normalize(p)
        print("normalized:", p)
