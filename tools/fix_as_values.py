"""修好 _as_values 被插到 @dataclass 与 class GuardState 之间的语法错位。"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\pipeline.py")
text = path.read_text(encoding="utf-8")

bad = '''@dataclass
def _as_values(value: object) -> tuple[object, ...]:
    """把可能是列表的对象值摊平成可逐个比较的值。"""
    if isinstance(value, (list, tuple, set)):
        return tuple(value)
    return (value,)

class GuardState:'''

good = '''def _as_values(value: object) -> tuple[object, ...]:
    """把可能是列表的对象值摊平成可逐个比较的值。"""
    if isinstance(value, (list, tuple, set)):
        return tuple(value)
    return (value,)


@dataclass
class GuardState:'''

if bad in text:
    path.write_text(text.replace(bad, good), encoding="utf-8")
    print("已修正")
else:
    print("未匹配")
    idx = text.find("_as_values")
    print(text[max(0, idx - 200):idx + 400])
