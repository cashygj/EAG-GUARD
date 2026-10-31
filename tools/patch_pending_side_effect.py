"""给守卫元素加 pending_side_effect()：任务该办的副作用一个都没做成？"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\integrations\agentdojo.py")
text = path.read_text(encoding="utf-8")

anchor = "    def consume_recovery_flag(self) -> bool:"
method = '''    def pending_side_effect(self) -> bool:
        """本任务有"办理类"工具可用，但一个副作用动作都没成功执行过。

        用途：模型把"一个动作被拒"当成"任务结束"时，收尾前再推它一次。
        只看授权工具集（T）里有没有副作用工具——T 是从用户请求推出来的，
        所以它同时代表"用户要办的事"。
        """
        scope = getattr(self.state, "scope", None)
        if scope is None:
            return False
        tools = getattr(self.guard, "tools", {}) or {}
        wants = [
            name for name in scope.tools
            if name in tools and not getattr(tools[name], "read_only", False)
        ]
        if not wants:
            return False
        done = {
            str(item.get("function"))
            for item in (self.executed or [])
        }
        return not any(name in done for name in wants)

'''
if "def pending_side_effect" not in text and anchor in text:
    text = text.replace(anchor, method + anchor, 1)
    path.write_text(text, encoding="utf-8")
    print("已加 pending_side_effect")
else:
    print("未加（可能已存在）")
