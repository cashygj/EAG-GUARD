"""把 run_all.ps1 重新写成 UTF-8 with BOM。

PowerShell 5.1 在没有 BOM 时会按 ANSI 读取 .ps1，中文字符串会被拆坏，
导致脚本无法解析。这里统一加上 BOM，顺便校验一次语法。
"""

from pathlib import Path

target = Path(r"D:\EAG-GUARD\run_all.ps1")
text = target.read_text(encoding="utf-8-sig")
target.write_text(text, encoding="utf-8-sig")
print("rewritten with BOM:", target)
print("first line:", text.splitlines()[0])
