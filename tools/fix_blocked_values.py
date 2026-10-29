"""修好 blocked_values 被插进 consume_recovery_flag 中间造成的缩进错。"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\integrations\agentdojo.py")
text = path.read_text(encoding="utf-8")

bad = '''        if self._recovery_pending:
            self._recovery_pending = False
        #: 被判定为注入、且出现在被拒动作里的值；输出审核只抹这些。
        self.blocked_values: set[str] = set()
            return True
        return False'''

good = '''        if self._recovery_pending:
            self._recovery_pending = False
            return True
        return False'''

if bad in text:
    path.write_text(text.replace(bad, good), encoding="utf-8")
    print("已修正 consume_recovery_flag")
else:
    print("未匹配")
