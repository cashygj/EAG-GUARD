"""输出审核：返回最终回答前的文本出口检查。

报告 §2.3 第 3 阶段：在返回最终回答前检查文本中是否带入了注入内容。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Callable, Iterable, Sequence

from .types import Decision, EvidenceItem, Trust

MIN_BLOCK = 32

_INSTRUCTION_PATTERNS = (
    re.compile(r"ignore (?:all )?(?:the )?(?:previous|prior|above) (?:instructions?|prompts?)", re.I),
    re.compile(r"disregard (?:the )?(?:previous|above)", re.I),
    re.compile(r"(?:please|now) (?:send|transfer|forward|pay|delete)\b", re.I),
    re.compile(r"忽略(?:之前|以上|前面)的?(?:所有)?(?:指令|要求|提示)"),
    re.compile(r"请(?:立即)?(?:发送|转账|转发|支付|删除)"),
)


@dataclass(frozen=True)
class AuditResult:
    text: str
    flagged: bool
    redactions: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()
    decision: Decision | None = None


class OutputAudit:
    """检测并裁剪：回答中与不可信内容逐字重合的长片段。"""

    def __init__(self, min_block: int = MIN_BLOCK,
                 complete: Callable[[str], str] | None = None) -> None:
        self.min_block = min_block
        self.complete = complete

    def audit(self, text: str, evidence: Sequence[EvidenceItem]) -> AuditResult:
        # 只审"用户没授权读的来源"。用户本来就让你读的那份材料，把它的内容
        # 写进回答是任务本身——裁掉它既毁效用，也防不住真正的注入。
        untrusted = [e for e in evidence if e.trust is Trust.UNTRUSTED and not e.authorized]
        redactions: list[str] = []
        findings: list[str] = []
        out = text

        for item in untrusted:
            for block in self._leaked_blocks(out, item.text):
                if block in out:
                    out = out.replace(block, "〔已移除外部内容〕")
                    redactions.append(block)
                    findings.append(f"回答逐字复述了来自 {item.source} 的内容")

        for pattern in _INSTRUCTION_PATTERNS:
            match = pattern.search(text)
            if match:
                findings.append(f"回答中出现指令式语句：{match.group(0)!r}")

        decision = Decision(
            stage="output",
            allowed=not redactions,
            reasons=tuple(findings) or (),
            detail={"redactions": len(redactions)},
        )
        return AuditResult(text=out, flagged=bool(findings),
                           redactions=tuple(redactions),
                           findings=tuple(dict.fromkeys(findings)),
                           decision=decision)

    def _leaked_blocks(self, text: str, source: str) -> list[str]:
        if not text or not source:
            return []
        matcher = SequenceMatcher(None, text, source, autojunk=False)
        blocks = []
        for match in matcher.get_matching_blocks():
            if match.size >= self.min_block:
                blocks.append(text[match.a:match.a + match.size])
        return blocks


class NullAudit:
    """关闭输出审核的消融臂。"""

    def audit(self, text: str, evidence: Sequence[EvidenceItem]) -> AuditResult:
        return AuditResult(text=text, flagged=False)
