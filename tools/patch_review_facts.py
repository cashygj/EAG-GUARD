"""答复复查时把"工具返回的原文片段"一并给它，让它照着抄。"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\bench\answer_review.py")
text = path.read_text(encoding="utf-8")

# 1) 提示词加"原文片段"段
text = text.replace(
    "【你的答复】\n{answer}\n",
    "【你的答复】\n{answer}\n\n"
    "【工具返回的原文片段（照抄这些值，不要改写、不要省略）】\n{facts}\n",
)

# 2) 构造函数接受证据回调
old_init = (
    "    def __init__(self, llm: Any) -> None:\n"
    "        self.llm = llm"
)
new_init = (
    "    def __init__(self, llm: Any, evidence: Any = None) -> None:\n"
    "        self.llm = llm\n"
    "        self.evidence = evidence      # 可选：返回最近证据的回调\n\n"
    "    def _facts(self, limit: int = 3, width: int = 700) -> str:\n"
    "        if self.evidence is None:\n"
    '            return "（无）"\n'
    "        try:\n"
    "            items = list(self.evidence())[-limit:]\n"
    "        except Exception:\n"
    '            return "（无）"\n'
    "        lines = []\n"
    "        for item in items:\n"
    '            body = getattr(item, "text", "") or ""\n'
    "            if body.strip():\n"
    '                src = getattr(item, "source", "?")\n'
    '                lines.append(f"- 来自 {src}：" + body.strip()[:width].replace(chr(10), " "))\n'
    '        return chr(10).join(lines) or "（无）"'
)
if old_init in text:
    text = text.replace(old_init, new_init)

# 3) 调用处带上 facts
text = text.replace(
    "prompt = INSTRUCTION.format(request=query, answer=answer[:3000])",
    "prompt = INSTRUCTION.format(request=query, answer=answer[:3000],\n                                    facts=self._facts())",
)

path.write_text(text, encoding="utf-8")
print("facts 段:", "{facts}" in text)
print("证据回调:", "self.evidence" in text)
