"""把「可操作原因」的计算提前到强弱反馈分叉之前，两个分支都用得上。

踩坑记录：第一次实现时把它加在了强反馈分支里，而 banking 走弱反馈，
导致这段代码在 banking 上一次都没执行（0 条轨迹包含该文案）。
"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\integrations\agentdojo.py")
text = path.read_text(encoding="utf-8")

# 1) 先把当前位于强反馈分支里的 actionable 计算整段剪出来
start_marker = "        # 「可操作原因」：报告要求拒绝时返回**可操作**的原因"
start = text.index(start_marker)
end_marker = '        actionable_block = "\n【正确的取值】'
end = text.index(end_marker, start)
end = text.index('"\n', text.index('"\n', end) + 1) + 2  # 覆盖 actionable_block 赋值两行
actionable_src = text[start:end]
text = text[:start] + text[end:]

# 2) 插到弱反馈分支之前（hint 计算完之后）
anchor = '        # 试过在拒绝时列出"你已读过的授权来源"'
idx = text.index(anchor)
text = text[:idx] + actionable_src + "\n" + text[idx:]

# 3) 弱反馈分支里也带上
old_weak = '''            parts.append(f"用户的请求是：「{self._request[:300]}」")
            parts.append("请继续把剩下的步骤做完。")
            return "\\n".join(parts)'''
new_weak = '''            if actionable_block:
                parts.append(actionable_block.strip())
            parts.append(f"用户的请求是：「{self._request[:300]}」")
            parts.append("请继续把剩下的步骤做完。")
            return "\\n".join(parts)'''
if old_weak in text:
    text = text.replace(old_weak, new_weak)
else:
    print("警告：弱反馈分支没匹配上")

path.write_text(text, encoding="utf-8")
print("可操作原因已移到分叉之前，并接入弱反馈分支")
