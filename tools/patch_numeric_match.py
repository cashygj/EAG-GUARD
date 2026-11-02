"""修数值等价：模型传 `10`，交易记录里是 `10.0`，原来匹配不上。

`_contains` 对短值（<3 字符）要求词边界，`(?<![\\w.])10(?![\\w.])` 匹配不到 `10.0`，
于是"退款 10 元"这类任务全部被判"金额无法归因"——banking 在强模型下的守卫负效应
主要就是这个（4 个净损失对里有 4 个是 amount 归因失败）。

修法：value_in 里对数值加"等价写法"变体（10 → 10.0 / 10.00 / 10）。
"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\provenance.py")
text = path.read_text(encoding="utf-8")

old = """    raw = str(value)
    for variant in [*date_variants(raw), *url_variants(raw)]:"""
new = """    raw = str(value)
    for variant in [*date_variants(raw), *url_variants(raw), *_numeric_variants(raw)]:"""
if old in text:
    text = text.replace(old, new)
else:
    print("警告：value_in 变体行未匹配")

helper = '''def _numeric_variants(raw: str) -> list[str]:
    """数值的等价写法：10 → 10.0 / 10.00；10.0 → 10。"""
    text = raw.strip().replace(",", "").lstrip("$€£¥")
    try:
        number = float(text)
    except ValueError:
        return []
    out = [f"{number:.1f}", f"{number:.2f}", str(number)]
    if number.is_integer():
        out.append(str(int(number)))
    return [v for v in dict.fromkeys(out) if v != raw]


'''
anchor = "def value_in(text: str, value: object) -> bool:"
if "_numeric_variants" not in text.split(anchor)[0]:
    text = text.replace(anchor, helper + anchor, 1)

path.write_text(text, encoding="utf-8")
print("已加数值变体:", "_numeric_variants" in text)
