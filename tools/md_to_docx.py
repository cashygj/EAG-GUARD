"""把总结 markdown 转成一份 Word 汇报稿。"""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

MD = Path(r"D:\EAG-GUARD\docs\32-总结汇报.md")
OUT = Path(r"D:\EAG-GUARD\docs\EAG-Guard重建总结汇报.docx")

doc = Document()
style = doc.styles["Normal"]
style.font.name = "微软雅黑"
style.font.size = Pt(10.5)

lines = MD.read_text(encoding="utf-8").splitlines()
table_buffer: list[list[str]] = []


def flush_table() -> None:
    global table_buffer
    if not table_buffer:
        return
    rows = [r for r in table_buffer if not set(r[0]) <= {"-", ":", " "}]
    if rows:
        table = doc.add_table(rows=len(rows), cols=len(rows[0]))
        table.style = "Light Grid Accent 1"
        for i, row in enumerate(rows):
            for j, cell in enumerate(row[: len(rows[0])]):
                table.cell(i, j).text = cell.strip()
    table_buffer = []


for raw in lines:
    line = raw.rstrip()
    if line.startswith("|"):
        cells = [c for c in line.strip("|").split("|")]
        table_buffer.append(cells)
        continue
    flush_table()

    if not line.strip():
        continue
    if line.startswith("# "):
        title = doc.add_heading(line[2:].strip(), level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif line.startswith("## "):
        doc.add_heading(line[3:].strip(), level=1)
    elif line.startswith("### "):
        doc.add_heading(line[4:].strip(), level=2)
    elif line.startswith("| "):
        pass
    elif line.lstrip().startswith(("- ", "* ")):
        doc.add_paragraph(line.lstrip()[2:].strip(), style="List Bullet")
    elif line.lstrip().startswith("> "):
        para = doc.add_paragraph(line.lstrip()[2:].strip())
        para.runs[0].italic = True
    else:
        doc.add_paragraph(line.strip())

flush_table()
OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print("已生成:", OUT)
