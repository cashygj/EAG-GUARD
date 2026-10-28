from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\pipeline.py")
text = path.read_text(encoding="utf-8")
bad = "from .parsing import (\\n    STRICT_PARAMS,"
good = "from .parsing import (\n    STRICT_PARAMS,"
if bad in text:
    text = text.replace(bad, good)
    path.write_text(text, encoding="utf-8")
    print("fixed")
else:
    for line in text.splitlines()[:25]:
        if "parsing import" in line:
            print("line:", repr(line))
