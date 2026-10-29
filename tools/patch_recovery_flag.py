"""给 EAGGuardElement 加"刚发生拦截"的标志与消费接口。"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\integrations\agentdojo.py")
text = path.read_text(encoding="utf-8")

# 1) 初始化
if "self._recovery_pending = False" not in text:
    text = text.replace(
        "        self._sanctioned: set[str] = set()",
        "        self._sanctioned: set[str] = set()\n        self._recovery_pending = False",
    )

# 2) 发出拒绝提示时置位
old_emit = ('            messages = [*messages, ChatUserMessage(\n'
            '                role="user", content=[text_content_block_from_string(text)])]')
new_emit = old_emit + "\n            self._recovery_pending = True"
if "self._recovery_pending = True" not in text and old_emit in text:
    text = text.replace(old_emit, new_emit)

# 3) 消费接口
anchor = "    # ------------------------------------------------------------------ 辅助"
method = (
    "    def consume_recovery_flag(self) -> bool:\n"
    '        """有一次刚发生的拦截还没被"续做"消费掉？消费掉并返回 True。"""\n'
    "        if self._recovery_pending:\n"
    "            self._recovery_pending = False\n"
    "            return True\n"
    "        return False\n\n"
)
if "consume_recovery_flag" not in text and anchor in text:
    text = text.replace(anchor, method + anchor, 1)

path.write_text(text, encoding="utf-8")
print("flag 初始化:", "self._recovery_pending = False" in text)
print("置位:", "self._recovery_pending = True" in text)
print("消费接口:", "consume_recovery_flag" in text)
