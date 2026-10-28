"""banking 改用"字段级严格"：收款人/金额可来自结构化字段，但不能来自正文。"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\bench\agentdojo_runner.py")
text = path.read_text(encoding="utf-8")

start = text.index("STRICT_PARAMS_BY_DOMAIN: dict[str, tuple[str, ...]] = {")
end = text.index("}", start) + 1

new = '''STRICT_PARAMS_BY_DOMAIN: dict[str, tuple[str, ...]] = {
    # 只认用户直接指定（暂不启用：实测会误杀"像上个月那样付"这类合法委托）
}

#: 字段级严格：付款字段必须来自结构化字段（账单的 IBAN/Total、交易的 recipient/amount）。
#: 证据切片之后这条是安全的——注入内容只出现在 subject 正文里，进不了字段。
FIELD_STRICT_PARAMS_BY_DOMAIN: dict[str, tuple[str, ...]] = {
    "banking": (
        "send_money.recipient",
        "send_money.amount",
        "schedule_transaction.recipient",
        "schedule_transaction.amount",
        "update_scheduled_transaction.recipient",
        "update_scheduled_transaction.amount",
    ),
}'''
text = text[:start] + new + text[end:]

# make_guard 里把 field_strict 也传进去
old_cfg = '''        config = replace(
            config,
            read_policy=policy.get("read_policy", config.read_policy),
            strict_params=STRICT_PARAMS_BY_DOMAIN.get(getattr(suite, "name", ""), config.strict_params),
        )'''
new_cfg = '''        config = replace(
            config,
            read_policy=policy.get("read_policy", config.read_policy),
            strict_params=STRICT_PARAMS_BY_DOMAIN.get(getattr(suite, "name", ""), config.strict_params),
            field_strict_params=FIELD_STRICT_PARAMS_BY_DOMAIN.get(
                getattr(suite, "name", ""), config.field_strict_params),
        )'''
if old_cfg in text:
    text = text.replace(old_cfg, new_cfg)
else:
    print("警告：make_guard 的 replace 调用没匹配上")

path.write_text(text, encoding="utf-8")
print("已改为字段级严格")
