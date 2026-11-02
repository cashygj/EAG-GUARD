"""数值等价只在"结构化字段比对"里生效，正文匹配保持严格。

教训：把数值变体加到 value_in（正文匹配）后，banking 同 39 对 UA 0.718 → 0.538——
正文里的数字也被当成来源，注入文本里的金额因此可被采信。
正确位置是字段比对：交易切片里有 `amount: 10.0` 字段，模型传 10，应判等价。
"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\provenance.py")
text = path.read_text(encoding="utf-8")

# 1) 撤销正文层的数值变体
text = text.replace(
    "    for variant in [*date_variants(raw), *url_variants(raw), *_numeric_variants(raw)]:",
    "    for variant in [*date_variants(raw), *url_variants(raw)]:",
)

# 2) 字段比对改成"等价"而非字符串相等
old = """                    hits = [
                        e for e in pool
                        if e.fields.get(param) is not None
                        and normalize(e.fields[param]) == needle
                    ]"""
new = """                    hits = [
                        e for e in pool
                        if e.fields.get(param) is not None
                        and _same_value(e.fields[param], value)
                    ]"""
if old in text:
    text = text.replace(old, new)
else:
    print("警告：字段比对块未匹配")

helper = '''def _same_value(left: object, right: object) -> bool:
    """结构化字段的等值判断：字符串相等，或数值等价（10 == 10.0）。"""
    if normalize(left) == normalize(right):
        return True
    try:
        return float(str(left).replace(",", "")) == float(str(right).replace(",", ""))
    except (TypeError, ValueError):
        return False


'''
anchor = "def value_in(text: str, value: object) -> bool:"
if "_same_value" not in text.split(anchor)[0]:
    text = text.replace(anchor, helper + anchor, 1)

path.write_text(text, encoding="utf-8")
print("正文数值变体已撤销:", "*_numeric_variants(raw)" not in text)
print("字段等值已加:", "_same_value" in text)
