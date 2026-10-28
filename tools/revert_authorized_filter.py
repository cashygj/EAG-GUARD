"""回退两处：provenance 的 authorized 过滤、测试里被自动补进去的 authorized=True。"""

import re
from pathlib import Path

# 1) provenance 回退
prov = Path(r"D:\EAG-GUARD\src\eag_guard\provenance.py")
text = prov.read_text(encoding="utf-8")
text = text.replace(
    """                    # 字段级委托必须同时满足：证据本身是"用户授权读取"的。
                    # 否则模型随手读一次未授权的交易列表，里面的任意账户都能
                    # 被当成"用户委托的收款人"（实测就是这样放过攻击者 IBAN 的）。
                    hits = [
                        e for e in pool
                        if e.authorized
                        and e.fields.get(param) is not None
                        and normalize(e.fields[param]) == needle
                    ]""",
    """                    hits = [
                        e for e in pool
                        if e.fields.get(param) is not None
                        and normalize(e.fields[param]) == needle
                    ]""",
)
prov.write_text(text, encoding="utf-8")
print("provenance 已回退")

# 2) 测试文件回退
tests = Path(r"D:\EAG-GUARD\tests\test_attribution.py")
t = tests.read_text(encoding="utf-8")
t = re.sub(r"\n\s*authorized=True,\n\)", "\n)", t)
# 处理被改成 "...  authorized=True,\n)" 后剩下的一行
t = re.sub(r"\n(\s*)authorized=True,\n\)", "\n)", t)
tests.write_text(t, encoding="utf-8")
print("test_attribution 已回退")
