from pathlib import Path

p = Path(r"D:\EAG-GUARD\tools\official_baseline.py")
t = p.read_text(encoding="utf-8")
old = '''            environment = suite.load_and_inject_default_environment(
                {inj_id: inj_task.INJECTIONS[inj_id]}
            )'''
new = '''            # 用攻击对象自己生成注入内容，再据此构造环境（官方跑法）
            injections = attack.attack(user_task, inj_task)
            environment = suite.load_and_inject_default_environment(injections)'''
if old in t:
    t = t.replace(old, new)
    p.write_text(t, encoding="utf-8")
    print("patched env injection")
else:
    print("pattern not found")
    idx = t.find("load_and_inject")
    print(t[idx - 200 : idx + 200])
