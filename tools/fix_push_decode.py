from pathlib import Path

p = Path(r"D:\EAG-GUARD\tools\push_via_api.py")
t = p.read_text(encoding="utf-8")
old = 'out = subprocess.run([str(GIT), "ls-files"], cwd=REPO, capture_output=True, text=True)'
new = (
    'out = subprocess.run([str(GIT), "ls-files"], cwd=REPO, capture_output=True,\n'
    '                         text=True, encoding="utf-8", errors="replace")'
)
if old in t:
    p.write_text(t.replace(old, new), encoding="utf-8")
    print("已修正解码")
else:
    print("未找到目标行")
