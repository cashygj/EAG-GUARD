"""给 slack 的对象参数加"字段级严格"，并回退解析器那条净负改动。"""

from pathlib import Path

# 1) 回退解析器的 objects 提示
parsing = Path(r"D:\EAG-GUARD\src\eag_guard\parsing.py")
t = parsing.read_text(encoding="utf-8")
t = t.replace(
    """2. objects 的类别必须是工具清单里标注的类别；**用户请求里点名的具体值都要写进去**
   （人名、频道名、文件名、邮箱地址……只要出现了、且属于某个工具的类别）。
   漏写会让该对象在执行时被判"不在授权范围"，任务直接做不完；
   用户完全没提到具体值时才留空；""",
    """2. objects 的类别必须是工具清单里标注的类别；用户没点名具体值就不要写；
   （试过要求"点名值都写进去"：slack 全域 ASR 9.52%→11.43%、UA 0.40→0.39，净负，已回退）""",
)
parsing.write_text(t, encoding="utf-8")
print("解析器提示已回退")

# 2) 给 slack 加字段级严格
runner = Path(r"D:\EAG-GUARD\src\eag_guard\bench\agentdojo_runner.py")
r = runner.read_text(encoding="utf-8")
start = r.index("FIELD_STRICT_PARAMS_BY_DOMAIN: dict[str, tuple[str, ...]] = {")
end = r.index("}", start) + 1
new = '''FIELD_STRICT_PARAMS_BY_DOMAIN: dict[str, tuple[str, ...]] = {
    # slack：用户/收件人这类对象参数必须是"结构化字段里的值"（消息的 sender/
    # recipient），不能是正文里出现的任意字符串。实测注入把新人名写进消息正文，
    # 就被当成了"委托来的对象"，据此把攻击者加进了频道。
    "slack": (
        "add_user_to_channel.user",
        "invite_user_to_slack.user",
        "remove_user_from_slack.user",
        "send_direct_message.recipient",
    ),
}'''
r = r[:start] + new + r[end:]
runner.write_text(r, encoding="utf-8")
print("slack 字段级严格已写入")
