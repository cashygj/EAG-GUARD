"""把模型的最终答复落进轨迹，便于诊断"答复内容不达标"这类失败。"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\bench\agentdojo_runner.py")
text = path.read_text(encoding="utf-8")

# 1) PairRun 增加字段
if "final_answer: str = \"\"" not in text:
    text = text.replace(
        "    executed: list[dict] = field(default_factory=list)\n"
        '    error: str = ""',
        "    executed: list[dict] = field(default_factory=list)\n"
        '    error: str = ""\n'
        '    final_answer: str = ""',
    )

# 2) to_dict 输出
if '"final_answer": self.final_answer' not in text:
    text = text.replace(
        '            "executed": self.executed,',
        '            "executed": self.executed,\n'
        '            "final_answer": self.final_answer,',
    )

# 3) 读回时填充
if 'final_answer=str(data.get("final_answer") or "")' not in text:
    text = text.replace(
        '            executed=list(data.get("executed") or []),',
        '            executed=list(data.get("executed") or []),\n'
        '            final_answer=str(data.get("final_answer") or ""),',
    )

# 4) 跑完一对后写入
old_assign = "        run.utility, run.security = bool(utility), bool(security)"
new_assign = (
    "        run.utility, run.security = bool(utility), bool(security)\n"
    "        run.final_answer = pipeline.final_answer() if hasattr(pipeline, \"final_answer\") else \"\""
)
if "run.final_answer = pipeline.final_answer()" not in text and old_assign in text:
    text = text.replace(old_assign, new_assign)

path.write_text(text, encoding="utf-8")
print("final_answer 字段:", "final_answer: str = \"\"" in text)
print("序列化:", '"final_answer": self.final_answer' in text)
print("读回:", 'final_answer=str(data.get("final_answer")' in text)
print("写入:", "run.final_answer = pipeline.final_answer()" in text)
