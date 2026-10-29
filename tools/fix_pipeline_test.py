"""更新测试：travel 的流水线末尾现在是 [answer_review, output_audit]。"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\tests\test_agentdojo_adapter.py")
text = path.read_text(encoding="utf-8")

old = """    pipeline = travel
    elements = pipeline._pipeline.elements
    loop = elements[-2]
    assert getattr(loop, "max_iters", None) == 1"""
new = """    pipeline = travel
    elements = pipeline._pipeline.elements
    # travel 末尾依次是「答复复查」和「输出审核」，循环在它们之前
    assert getattr(elements[-2], "name", "") == "answer_review"
    loop = elements[-3]
    assert getattr(loop, "max_iters", None) == 1"""

if old in text:
    path.write_text(text.replace(old, new), encoding="utf-8")
    print("测试已更新")
else:
    print("未匹配")
