from docx import Document

path = r"D:\Program Files (x86)\xwechat_files\wxid_qt0mzs5wekag22_65ad\msg\file\2026-10\EAG-Guard阶段性研究报告.docx"
doc = Document(path)

keys = ["gpt", "GPT", "qwen", "Qwen", "通义", "模型", "temperature", "温度", "快照", "snapshot"]
for i, p in enumerate(doc.paragraphs):
    text = p.text.strip()
    if text and any(k in text for k in keys):
        print(f"[{i}] {text[:300]}\n")
