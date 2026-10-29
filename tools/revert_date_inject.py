"""回退"把当前日期写进系统提示"：实测 workspace 0.5234 → 0.4875，净负。"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\bench\agentdojo_runner.py")
text = path.read_text(encoding="utf-8")

start = text.index('    # 告诉模型"今天是哪天"')
end = text.index("    if hint:", start)
text = text[:start] + (
    "    # 试过把环境的 current_day（2024-05-15）写进系统提示，想让模型别把\n"
    '    # "May 26th" 猜成 2023 年：实测 workspace UA 0.5234 → 0.4875、ASR 升，净负，已回退。\n'
) + text[end:]
path.write_text(text, encoding="utf-8")
print("已回退日期注入")
