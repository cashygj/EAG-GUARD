"""证据切片：把一次工具返回切成"一条记录一条证据"，并抽出结构化字段。

这是报告 §2.3 "工具返回被切分为带来源标签的证据" 与 §2.2 "字段级溯源可达性
（FPR）" 的实现。没有它，收款人只能靠字符串匹配判断，而攻击者把 IBAN 写进
交易记录的 subject 正文里就能冒充"账单上的收款人"。

切片之后：字段级委托只在**结构化字段**里找值——
  - 账单：Total → amount，IBAN → recipient；
  - 交易记录：每笔交易的 recipient/amount/sender/date 各自成一条证据。
攻击者写在 subject 里的 IBAN 只是文本，不构成任何字段，因此不会被当成收款人。
"""

from __future__ import annotations

import re

# Transaction(id=5, sender='GB29...', recipient='me', amount=10.0,
#             subject='Sushi dinner', date='2022-03-07', recurring=False)
_TRANSACTION = re.compile(
    r"Transaction\(id=(?P<id>\d+),\s*"
    r"sender='(?P<sender>[^']*)',\s*"
    r"recipient='(?P<recipient>[^']*)',\s*"
    r"amount=(?P<amount>[\d.]+),\s*"
    r"subject='(?P<subject>[^']*)',\s*"
    r"date='(?P<date>[^']*)'"
)

_BILL_TOTAL = re.compile(r"Total\s+([0-9]+(?:\.[0-9]+)?)")
_BILL_IBAN = re.compile(r"IBAN:\s*([A-Z0-9]+)")

# slack: Message(sender='Bob', recipient='general', body='...')
_SLACK_MESSAGE = re.compile(
    r"Message\(sender='(?P<sender>[^']*)',\s*"
    r"recipient='(?P<recipient>[^']*)',\s*"
    r"body='(?P<body>.*?)'\)",
    re.DOTALL,
)

# workspace email: Email(id_='2', sender='...', recipients=['...'], subject='...', body='...')
_EMAIL = re.compile(
    r"Email\(id_='(?P<id>[^']*)',\s*"
    r"sender='(?P<sender>[^']*)',\s*"
    r"recipients=\[(?P<recipients>[^\]]*)\],\s*"
    r"cc=\[[^\]]*\],\s*bcc=\[[^\]]*\],\s*"
    r"subject='(?P<subject>[^']*)',\s*"
    r"body='(?P<body>.*?)',\s*status=",
    re.DOTALL,
)


def slice_evidence(tool: str, text: str) -> list[tuple[str, dict[str, str], str]]:
    """返回 [(切片标签, 字段字典, 该切片的文本)]。没有可切的东西就返回空。"""
    if tool in {"get_most_recent_transactions", "get_scheduled_transactions"}:
        slices = []
        for match in _TRANSACTION.finditer(text):
            fields = {
                "recipient": match.group("recipient"),
                "sender": match.group("sender"),
                "amount": match.group("amount"),
                "date": match.group("date"),
                "subject": match.group("subject"),
            }
            slices.append((f"tx{match.group('id')}", fields, match.group(0)))
        return slices

    if tool in {"read_channel_messages", "read_inbox"}:
        # 每条消息一条证据：发件人、收件人、正文各自成字段。
        # 好处是"这个网址/这句话出自谁的消息"变成可判定的，
        # 而不是把整个频道的内容揉成一团。
        slices = []
        for index, match in enumerate(_SLACK_MESSAGE.finditer(text)):
            fields = {
                "sender": match.group("sender"),
                "recipient": match.group("recipient"),
                "body": match.group("body"),
            }
            slices.append((f"msg{index}", fields, match.group(0)))
        return slices

    if tool in {"search_emails", "get_received_emails", "get_sent_emails",
                "get_unread_emails"}:
        # 每封邮件一条证据：发件人、收件人、主题、正文。
        slices = []
        for match in _EMAIL.finditer(text):
            recipients = [r.strip().strip("'\"") for r in match.group("recipients").split(",")
                          if r.strip()]
            fields = {
                "sender": match.group("sender"),
                "recipients": ";".join(recipients),
                "subject": match.group("subject"),
                "body": match.group("body"),
            }
            slices.append((f"mail{match.group('id')}", fields, match.group(0)))
        return slices

    if tool == "read_file":
        fields: dict[str, str] = {}
        total = _BILL_TOTAL.search(text)
        iban = _BILL_IBAN.search(text)
        if total:
            fields["amount"] = total.group(1)
        if iban:
            fields["recipient"] = iban.group(1)
        if fields:
            return [("bill", fields, text)]
    return []
