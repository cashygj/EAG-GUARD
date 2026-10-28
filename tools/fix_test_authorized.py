"""修掉上一步自动补丁造成的语法错误：把 authorized=True 放回 EvidenceItem 的参数列表里。"""

import re
from pathlib import Path

path = Path(r"D:\EAG-GUARD\tests\test_attribution.py")
text = path.read_text(encoding="utf-8")

# 把 "...  <内容>    authorized=True,\n)" 这种写法改回
#   "...", authorized=True,\n)
pattern = re.compile(r'(\n\s*[^\n]*?)\s{4}authorized=True,\n\)')

def repl(match: re.Match[str]) -> str:
    head = match.group(1).rstrip()
    if not head.endswith(","):
        head += ","
    return head + "\n                           authorized=True,\n)"

new_text, count = pattern.subn(repl, text)
path.write_text(new_text, encoding="utf-8")
print(f"修正 {count} 处")
