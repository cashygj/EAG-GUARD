from pathlib import Path

p = Path(r"D:\EAG-GUARD\tools\official_baseline.py")
t = p.read_text(encoding="utf-8")
t = t.replace(
    "                    agent_pipeline=attack, user_task=user_task,",
    "                    agent_pipeline=pipeline, user_task=user_task,",
)
p.write_text(t, encoding="utf-8")
print("patched: 用 pipeline 而不是 attack 对象")
