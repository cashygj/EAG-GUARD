from docx import Document
import re

path = r"D:\Program Files (x86)\xwechat_files\wxid_qt0mzs5wekag22_65ad\msg\file\2026-10\EAG-Guard阶段性研究报告.docx"
doc = Document(path)

keys = ["只读", "读操作", "写操作", "副作用", "读取", "守卫", "拦截", "放行", "动作"]
for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if not t:
        continue
    if any(k in t for k in ["只读", "副作用", "写操作", "读取", "读操作"]):
        print(f"[{i}] {t[:400]}\n")
