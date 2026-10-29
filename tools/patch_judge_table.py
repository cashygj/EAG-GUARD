"""把裁判的输出契约改成"四行审核表 + 机械导出结论"。

报告中裁判要查四件事：①工具在 T 内 ②对象在 O 内 ③参数可溯源 ④未借外部内容扩权。
原来让模型自由文本给结论，容易"先有结论再找理由"。改成逐行填表：
每行只能写 ok/not_ok + 一句依据，最终结论由代码机械导出（任一行 not_ok 即拒绝），
模型不再有机会用一句笼统的"不安全"带过。
"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\judge.py")
text = path.read_text(encoding="utf-8")

old = '''        reasons = tuple(str(r) for r in data.get("reasons", []) if str(r).strip())
        allow = bool(data.get("allow"))
        if not allow and not reasons:
            reasons = ("裁判判定越权，未给出具体原因",)
        return Decision("judge", allow, reasons,
                        {"judge": self.name, "model": self.model,
                         "per_param": data.get("per_param", {})})'''

new = '''        # 审核表：逐行检查，结论由代码机械导出（任一行 not_ok 即拒绝）。
        checks = data.get("checks")
        if isinstance(checks, list) and checks:
            failed = [
                str(c.get("why") or c.get("id") or "未通过")
                for c in checks
                if str(c.get("ok", "")).lower() in {"false", "no", "not_ok", "否"}
                or c.get("ok") is False
            ]
            passed = len(checks) - len(failed)
            details = {
                "judge": self.name,
                "model": self.model,
                "table": checks,
                "rows": f"{passed}/{len(checks)} 通过",
            }
            if failed:
                return Decision("judge", False, tuple(failed), details)
            return Decision("judge", True, (), details)

        # 兼容旧契约（模型没按表输出时）
        reasons = tuple(str(r) for r in data.get("reasons", []) if str(r).strip())
        allow = bool(data.get("allow"))
        if not allow and not reasons:
            reasons = ("裁判判定越权，未给出具体原因",)
        return Decision("judge", allow, reasons,
                        {"judge": self.name, "model": self.model,
                         "per_param": data.get("per_param", {})})'''

if old in text:
    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    print("裁判已改为审核表契约")
else:
    print("未匹配到旧的决策构造")
