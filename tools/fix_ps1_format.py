from pathlib import Path

target = Path(r"D:\EAG-GUARD\run_all.ps1")
text = target.read_text(encoding="utf-8-sig")
bad = '{0,-34} {1,>8} {2,>8}  {3}'
good = '{0,-34} {1,8} {2,8}  {3}'
count = text.count(bad)
text = text.replace(bad, good)
target.write_text(text, encoding="utf-8-sig")
print(f"replaced {count} format strings")
