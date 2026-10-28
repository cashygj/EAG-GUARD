from pathlib import Path

path = Path(r"D:\EAG-GUARD\tests\test_regressions.py")
text = path.read_text(encoding="utf-8")
bad = '    fake_call = type("C", (), {"function": "send_email"})()\\n    notice = element._recovery_notice([(fake_call, record)])'
good = (
    '    fake_call = type("C", (), {"function": "send_email"})()\n'
    '    notice = element._recovery_notice([(fake_call, record)])'
)
if bad in text:
    path.write_text(text.replace(bad, good), encoding="utf-8")
    print("fixed")
else:
    print("pattern not found")
    for i, line in enumerate(text.splitlines(), 1):
        if "fake_call" in line:
            print(i, repr(line))
