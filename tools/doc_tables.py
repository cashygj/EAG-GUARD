from docx import Document

path = r"D:\Program Files (x86)\xwechat_files\wxid_qt0mzs5wekag22_65ad\msg\file\2026-10\EAG-Guard阶段性研究报告.docx"
doc = Document(path)

for ti, table in enumerate(doc.tables):
    print(f"===== 表 {ti}（{len(table.rows)} 行 × {len(table.columns)} 列）=====")
    for row in table.rows:
        cells = [c.text.strip().replace("\n", " ") for c in row.cells]
        print(" | ".join(cells))
    print()
