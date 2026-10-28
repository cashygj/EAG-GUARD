import io
from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\integrations\agentdojo.py")
text = path.read_text(encoding="utf-8")

old = '        return value.strip().strip("\'`""").strip().casefold()'
new = (
    '        return value.strip().strip("\\\'\\"`").strip().casefold()'
)
if old in text:
    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    print("patched")
else:
    print("old line not found")
    for line in text.splitlines():
        if "casefold()" in line and "strip" in line:
            print("found:", repr(line))
