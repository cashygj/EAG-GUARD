"""删掉 DOMAIN_SYSTEM_HINTS 里重复的 banking 条目（旧的规则版），只保留流程版。"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\bench\agentdojo_runner.py")
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

# 找到 dict 定义之后、第二个 "banking": ( 开始的旧条目
dict_start = next(i for i, line in enumerate(lines) if line.startswith("DOMAIN_SYSTEM_HINTS"))
banking_lines = [i for i, line in enumerate(lines)
                 if line.strip().startswith('"banking": (') and i > dict_start]
if len(banking_lines) != 2:
    print("预期 2 个 banking 提示条目，实际", len(banking_lines))
    raise SystemExit(1)

old_start = banking_lines[1]
old_end = old_start
while not lines[old_end].strip().startswith("),"):
    old_end += 1
del lines[old_start:old_end + 1]

path.write_text("".join(lines), encoding="utf-8")
print(f"已删除重复条目：第 {old_start + 1}-{old_end + 1} 行")
