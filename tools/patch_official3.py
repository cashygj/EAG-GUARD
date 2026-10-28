from pathlib import Path

p = Path(r"D:\EAG-GUARD\tools\official_baseline.py")
t = p.read_text(encoding="utf-8")
old = """                utility, security = suite.run_task_with_pipeline(
                    agent_pipeline=attack, user_task=user_task,
                    injection_task=inj_task, environment=environment,
                )"""
new = """                utility, security = suite.run_task_with_pipeline(
                    agent_pipeline=attack, user_task=user_task,
                    injection_task=inj_task, injections=injections,
                    environment=environment,
                )"""
if old in t:
    t = t.replace(old, new)
    p.write_text(t, encoding="utf-8")
    print("patched signature")
else:
    print("not found")
