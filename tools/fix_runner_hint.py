"""修复被替换脚本切坏的 travel 提示块：补回后面被吞掉的代码。"""

from pathlib import Path

head_path = Path(r"D:\EAG-GUARD\_tmp\runner_head.py")
path = Path(r"D:\EAG-GUARD\src\eag_guard\bench\agentdojo_runner.py")

head = head_path.read_text(encoding="utf-8")
# HEAD 里"travel 提示结束"到"TaskPipeline.__init__ 的 self._pipeline"之间的原文
start_marker = '值要照抄工具返回的原文，不要改写、不要省略。"'
i = head.index(start_marker) + len(start_marker)
end_marker = "        self._pipeline = agentdojo_pipeline"
j = head.index(end_marker)
restored_block = head[i:j]

text = path.read_text(encoding="utf-8")
broken_tail = '按上面 5 步做。）                 llm=None) -> None:\n'
if broken_tail in text:
    text = text.replace(broken_tail, "按上面 5 步做。）", 1)
    # 在 travel 提示块结束后补回被吞掉的代码
    marker = "按上面 5 步做。）"
    k = text.index(marker) + len(marker)
    text = text[:k] + restored_block + text[k:]
    path.write_text(text, encoding="utf-8")
    print("已补回被吞掉的代码，长度:", len(restored_block))
else:
    print("未匹配到损坏处")
