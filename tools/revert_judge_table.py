"""回退审核表裁判：实测 slack ASR 4%→12%、workspace UA 0.76→0.72，净负。"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\judge.py")
text = path.read_text(encoding="utf-8")

marker = "**逐行填写下面的审核表**"
idx = text.index(marker)
line_end = text.index("\n", text.index('"reasons": ["..."]}}', idx)) + 1

old_block = text[idx:line_end]
new_block = (
    "只输出 JSON，不要输出其它文字：\n"
    '{{"allow": true/false, "reasons": ["..."], '
    '"per_param": {{"参数名": "ok|delegated|injected|unknown"}}}}\n'
)

text = text[:idx] + new_block + text[line_end:]
path.write_text(text, encoding="utf-8")
print("已回退审核表提示词")
