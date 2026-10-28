"""回退：banking 的付款字段改回"只认用户直接指定"。

字段级 strict（允许来自账单/交易的字段）实测：ASR 0.69% → 2.78%，
效用只从 0.5417 升到 0.5486（噪声级）。净负，回退。
"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\bench\agentdojo_runner.py")
text = path.read_text(encoding="utf-8")

start = text.index("STRICT_PARAMS_BY_DOMAIN: dict[str, tuple[str, ...]] = {")
end = text.index("#: 字段级严格", start)

new = '''STRICT_PARAMS_BY_DOMAIN: dict[str, tuple[str, ...]] = {
    # 资金流向字段：只认用户直接指定。
    # 试过放宽成"可来自账单/交易的字段"（配合证据切片），实测 ASR 0.69% → 2.78%，
    # 效用只 +0.007，净负，故保持窄口径。
    "banking": (
        "send_money.recipient",
        "schedule_transaction.recipient",
        "update_scheduled_transaction.recipient",
    ),
}

'''
text = text[:start] + new + text[end:]
path.write_text(text, encoding="utf-8")
print("已回退为 user-only strict")
