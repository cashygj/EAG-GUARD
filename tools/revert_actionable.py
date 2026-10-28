"""回退「可操作原因」（给出正确取值）这一段。

实测（banking 全域 144 对）：
  只说越权        0.69% / 0.5417
  给出正确取值    2.08% / 0.5347
效用无提升、ASR 反而升，净负。保留窄口径的拒绝文案。
"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\integrations\agentdojo.py")
text = path.read_text(encoding="utf-8")

start = text.index("        # 「可操作原因」：报告要求拒绝时返回**可操作**的原因")
end = text.index('        # 试过在拒绝时列出"你已读过的授权来源"')

replacement = '''        # 试过两种"更可操作"的拒绝文案：
        #   1) 列出"你已读过的授权来源"——修好 0 对、弄坏 2 对；
        #   2) 直接给出已授权证据里的正确取值（"收款人应是 UK12..."）——
        #      banking 全域 0.5417 → 0.5347、ASR 0.69% → 2.08%。
        # 两者都净负，故拒绝文案保持"说清状态 + 指出不该重试什么"。
'''
text = text[:start] + replacement + text[end:]

# 弱反馈分支里引用 actionable_block 的两行也去掉
text = text.replace(
    '''            if actionable_block:
                parts.append(actionable_block.strip())
''',
    "",
).replace(
    '''            + actionable_block
''',
    "",
)
path.write_text(text, encoding="utf-8")
print("已回退可操作原因")
