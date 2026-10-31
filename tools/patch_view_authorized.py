"""让裁判视图区分"用户点名的材料"与"其他不可信内容"。

原来 origins 只给来源标签（inbox/slack/web），裁判看到 "Slack 的返回" 就认为
不可信，于是把"顺着用户指定消息里的网址取值"判成扩权——slack 8 对任务因此全挂。
这里给已授权证据加上标记，裁判一眼能看出"这份材料是用户点名要读的"。
"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\pipeline.py")
text = path.read_text(encoding="utf-8")

old = """                origins={
                    a.param: tuple(dict.fromkeys(
                        ev.source
                        for ev in (by_id.get(i) for i in a.attribution.evidence_ids)
                        if ev is not None
                    ))
                    for a in reviewable
                },"""
new = """                origins={
                    a.param: tuple(dict.fromkeys(
                        # 标明"这份材料是用户点名要读的"，裁判据此判断
                        # "顺着它取值"属于任务本身，而不是看来源标签猜。
                        f"{ev.producer or ev.source}"
                        + ("（用户点名的材料）" if ev.authorized else "")
                        for ev in (by_id.get(i) for i in a.attribution.evidence_ids)
                        if ev is not None
                    ))
                    for a in reviewable
                },"""
if old in text:
    path.write_text(text.replace(old, new), encoding="utf-8")
    print("视图已标注授权来源")
else:
    print("未匹配")
