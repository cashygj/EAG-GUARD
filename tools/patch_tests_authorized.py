"""字段级委托现在要求证据本身是"用户授权读取"的，测试里的证据要标 authorized=True。"""

from pathlib import Path

for name in ("test_attribution.py", "test_pipeline_mock.py", "test_scope.py",
             "test_agentdojo_adapter.py"):
    path = Path(r"D:\EAG-GUARD\tests") / name
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    original = text
    # 在 EvidenceItem(...) 的构造里，若没有 authorized 参数就补上 True
    out_lines = []
    buffer = []
    inside = False
    depth = 0
    for line in text.splitlines(keepends=True):
        if "EvidenceItem(" in line:
            inside = True
            depth = 0
        if inside:
            depth += line.count("(") - line.count(")")
            buffer.append(line)
            if depth <= 0:
                block = "".join(buffer)
                if "authorized" not in block:
                    block = block.rstrip()
                    if block.endswith(")"):
                        block = block[:-1] + "    authorized=True,\n)"
                    block += "\n"
                out_lines.append(block)
                buffer = []
                inside = False
            continue
        out_lines.append(line)
    new_text = "".join(out_lines)
    if new_text != original:
        path.write_text(new_text, encoding="utf-8")
        print(f"{name}: 已补 authorized=True")
    else:
        print(f"{name}: 无需修改")
