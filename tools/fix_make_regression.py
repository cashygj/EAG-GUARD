"""修 make_regression.py 里被写坏的多行替换。"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\tools\make_regression.py")
text = path.read_text(encoding="utf-8")

bad = (
    '            if (domain, data["user_task"], data["injection_task"]) in EXCLUDE:\\n'
    "                continue\\n"
    '            if other["utility"] and not data["utility"]:'
)
good = (
    '            if (domain, data["user_task"], data["injection_task"]) in EXCLUDE:\n'
    "                continue\n"
    '            if other["utility"] and not data["utility"]:'
)
text = text.replace(bad, good)
path.write_text(text, encoding="utf-8")
print("已修正:", "\\n" not in text)
