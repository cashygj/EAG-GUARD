"""输出审核收窄：只抹掉守卫判为 injected 的值，不再按"未授权证据重合"整段裁剪。

实测（travel 20 题，同一批任务）：
  审核开启  UA 0.25
  审核关闭  UA 0.55
说明原来的审核在摧毁合法答案——它把"餐厅评分/营业时间"这类来自查询结果的内容
也当成泄露抹掉了。报告里 travel 开审核只损失 0.014 效用，说明他们的审核窄得多。
"""

from pathlib import Path

# 1) audit.py：新增 blocked 参数，只抹这些值
audit_path = Path(r"D:\EAG-GUARD\src\eag_guard\audit.py")
text = audit_path.read_text(encoding="utf-8")

old_sig = "    def audit(self, text: str, evidence: Sequence[EvidenceItem]) -> AuditResult:"
new_sig = ("    def audit(self, text: str, evidence: Sequence[EvidenceItem],\n"
           "              blocked: Sequence[str] | None = None) -> AuditResult:")
text = text.replace(old_sig, new_sig, 1)

old_body = '''        untrusted = [e for e in evidence if e.trust is Trust.UNTRUSTED and not e.authorized]
        redactions: list[str] = []
        findings: list[str] = []
        out = text

        for item in untrusted:
            for block in self._leaked_blocks(out, item.text):
                if block in out:
                    out = out.replace(block, "〔已移除外部内容〕")
                    redactions.append(block)
                    findings.append(f"回答逐字复述了来自 {item.source} 的内容")
'''
new_body = '''        redactions: list[str] = []
        findings: list[str] = []
        out = text

        # 只抹"守卫判定为注入的值"（来自被拒动作的 injected 参数）。
        # 不要按"与未授权证据重合"整段裁剪：合法任务的答案本来就取自查询结果，
        # 那样会把正确答案一起抹掉（实测 travel UA 0.55 → 0.25）。
        for value in dict.fromkeys(str(v) for v in (blocked or ())):
            if len(value) >= 8 and value in out:
                out = out.replace(value, "〔已移除外部内容〕")
                redactions.append(value)
                findings.append(f"回答带入了被判为注入的内容：{value[:40]!r}")
'''
if old_body in text:
    text = text.replace(old_body, new_body)
else:
    print("警告：audit 主体未匹配")

text = text.replace(
    "    def audit(self, text: str, evidence: Sequence[EvidenceItem]) -> AuditResult:\n        return AuditResult(text=text, flagged=False)",
    "    def audit(self, text: str, evidence: Sequence[EvidenceItem],\n"
    "              blocked: Sequence[str] | None = None) -> AuditResult:\n"
    "        return AuditResult(text=text, flagged=False)",
)
audit_path.write_text(text, encoding="utf-8")
print("audit.py 已收窄")

# 2) agentdojo.py：拒绝时记录 injected 值；OutputAuditElement 传进去
adapter = Path(r"D:\EAG-GUARD\src\eag_guard\integrations\agentdojo.py")
a = adapter.read_text(encoding="utf-8")

if "self.blocked_values" not in a:
    a = a.replace(
        "        self._recovery_pending = False",
        "        self._recovery_pending = False\n"
        "        #: 被判定为注入、且出现在被拒动作里的值；输出审核只抹这些。\n"
        "        self.blocked_values: set[str] = set()",
    )

if "self.blocked_values.update" not in a:
    a = a.replace(
        "            else:\n                denied.append((call, record))",
        "            else:\n"
        "                denied.append((call, record))\n"
        "                for item in record.attributions:\n"
        "                    if item.provenance is Provenance.INJECTED:\n"
        "                        self.blocked_values.add(str(item.value))",
    )

if "blocked=getattr" not in a:
    a = a.replace(
        "        result = self.audit.audit(text, self.audit_evidence) if hasattr(self, 'audit_evidence') else self.audit.audit(text, [])",
        "        result = self.audit.audit(text, self.audit_evidence, blocked=self.blocked)",
    )
adapter.write_text(a, encoding="utf-8")
print("adapter 记录 blocked_values:", "self.blocked_values" in a)
