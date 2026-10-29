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

    def audit(self, text: str, evidence: Sequence[EvidenceItem],
              blocked: Sequence[str] | None = None) -> AuditResult:
        # 只审"用户没授权读的来源"。用户本来就让你读的那份材料，把它的内容
        # 写进回答是任务本身——裁掉它既毁效用，也防不住真正的注入。
        redactions: list[str] = []
        findings: list[str] = []
        out = text

        # 试过"抹掉被拒动作里的 injected 参数值"：会误伤合法取值——日历事件的
        # 地址来自查询结果，被拒后也进了黑名单，答复里的地址就被抹掉，任务直接失败。
        # 净负，不再使用；只保留下面那条"既像指令、又有出处"的窄规则。

        # 纯文本注入：答复里"既像指令、又确实出自不可信内容"的句子要抹掉。
        # 这类注入不在工具调用面上，守卫拦不到，只能靠输出端。
        # 两个条件同时成立才动手：光"像指令"会误伤正常措辞，
        # 光"有出处"会把合法事实抹掉（旧口径就是后者，travel UA 0.55 → 0.25）。
        for item in evidence:
            if item.trust is not Trust.UNTRUSTED:
                continue
            for sentence in re.split(r"(?<=[。！？.!?])\s*", out):
                if len(sentence) < self.min_block or sentence not in item.text:
                    continue
                if any(p.search(sentence) for p in _INSTRUCTION_PATTERNS):
                    out = out.replace(sentence, "〔已移除外部内容〕")
                    redactions.append(sentence)
                    findings.append(f"回答带入了外部内容里的指令（来自 {item.source}）")

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

    def audit(self, text: str, evidence: Sequence[EvidenceItem],
              blocked: Sequence[str] | None = None) -> AuditResult:
        return AuditResult(text=text, flagged=False)
