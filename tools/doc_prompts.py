from docx import Document
import re

path = r"D:\Program Files (x86)\xwechat_files\wxid_qt0mzs5wekag22_65ad\msg\file\2026-10\EAG-Guard阶段性研究报告.docx"
doc = Document(path)

keys = ["提示词", "系统提示", "prompt", "优化", "指令", "提示", "话术", "模板"]
for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if not t:
        continue
    if any(k in t for k in keys):
        print(f"[{i}] {t}\n")
