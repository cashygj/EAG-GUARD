"""修好 final_answer 赋值被插到 try 块外面的缩进错误。"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\bench\agentdojo_runner.py")
text = path.read_text(encoding="utf-8")

bad = (
    "            run.utility, run.security = bool(utility), bool(security)\n"
    '        run.final_answer = pipeline.final_answer() if hasattr(pipeline, "final_answer") else ""\n'
    "        except Exception as exc:"
)
good = (
    "            run.utility, run.security = bool(utility), bool(security)\n"
    "            run.final_answer = (\n"
    '                pipeline.final_answer() if hasattr(pipeline, "final_answer") else ""\n'
    "            )\n"
    "        except Exception as exc:"
)

if bad in text:
    path.write_text(text.replace(bad, good), encoding="utf-8")
    print("已修正缩进")
else:
    print("未匹配；当前片段：")
    idx = text.find("run.utility, run.security")
    print(text[idx - 60 : idx + 320])
