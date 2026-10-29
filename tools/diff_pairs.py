"""列出两个 run 之间"一个过、一个挂"的对，用于构造回归集。"""

import json
import sys
from pathlib import Path


def load(run: Path) -> dict[str, bool]:
    out = {}
    for path in run.glob("*.json"):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("error"):
            continue
        out[path.name] = bool(data["utility"])
    return out


a = load(Path(sys.argv[1]))
b = load(Path(sys.argv[2]))
common = sorted(set(a) & set(b))
only_a = [k for k in common if a[k] and not b[k]]
only_b = [k for k in common if b[k] and not a[k]]
print(f"{sys.argv[1]} 过、{sys.argv[2]} 挂：{len(only_a)}")
for name in only_a[:12]:
    print("   ", name.replace(".json", ""))
print(f"{sys.argv[2]} 过、{sys.argv[1]} 挂：{len(only_b)}")
for name in only_b[:12]:
    print("   ", name.replace(".json", ""))
