"""URL 匹配忽略协议/www 前缀差异。

实测（slack user_task_11）：邮件里写 `www.dora-website.com`，模型调用
`http://www.dora-website.com`；逐字匹配失败 → 判"只出现在不可信内容" →
整条委托链断掉，8 对任务全挂。
"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\provenance.py")
text = path.read_text(encoding="utf-8")

old = "            hits = [e for e in ctx.untrusted() if value_in(normalize(e.text), value)]"
new = """            hits = [
                e for e in ctx.untrusted()
                if value_in(normalize(e.text), value)
                or value_in(normalize(e.text), _url_forms(value))
            ]"""
if old in text:
    text = text.replace(old, new)
else:
    print("警告：匹配行未命中")

helper = '''def _url_forms(value: object) -> str:
    """把 URL 归一成"去掉协议与 www 前缀"的形式，用于文本匹配。"""
    text = str(value).strip()
    for prefix in ("https://", "http://", "www."):
        if text.lower().startswith(prefix):
            text = text[len(prefix):]
    return text.rstrip("/")


'''
anchor = "def _as_values" if "def _as_values" in text else None
if "_url_forms" not in text.split("class Attributor")[0]:
    if anchor:
        text = text.replace(anchor, helper + anchor, 1)
    else:
        # 放到文件里第一个 def 之前
        idx = text.index("\ndef ")
        text = text[:idx] + "\n" + helper + text[idx + 1:]

path.write_text(text, encoding="utf-8")
print("URL 归一:", "_url_forms" in text)
print("匹配已改:", "_url_forms(value)" in text)
