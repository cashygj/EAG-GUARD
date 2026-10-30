"""修：空参数值（'' / None / 空列表）不该参与溯源判定。

实测 travel user_task_12 的 send_email 被拒，理由是
`参数 attachments='' 无法归因到任何授权`、`cc=''`、`bcc=''`——
模型只是把可选参数留空，这不该算越权。
"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\pipeline.py")
text = path.read_text(encoding="utf-8")

old = """            for attr in attributions:
                # 硬规则：只出现在不可信内容里、没有被委托的 URL 一律不读。"""
new = """            for attr in attributions:
                # 空值不参与溯源：模型把可选参数留空（cc=''、attachments=[]）
                # 不是越权。实测这条把 travel 的 send_email 整条拒掉了。
                if _is_blank(attr.value):
                    continue
                # 硬规则：只出现在不可信内容里、没有被委托的 URL 一律不读。"""

if old in text:
    text = text.replace(old, new)
else:
    print("警告：循环锚点未匹配")

helper = '''def _is_blank(value: object) -> bool:
    """空字符串、None、空列表/空字典都算"没填"。"""
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip() or value.strip() in {"[]", "{}", "None", "null"}
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


'''
anchor = "def _as_values(value: object) -> tuple[object, ...]:"
if "_is_blank" not in text.split(anchor)[0]:
    text = text.replace(anchor, helper + anchor, 1)

path.write_text(text, encoding="utf-8")
print("空值豁免:", "_is_blank(attr.value)" in text)
print("辅助函数:", "def _is_blank" in text)
