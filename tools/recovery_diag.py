"""诊断：守卫弄挂的对里，模型在第一次被拦之后还尝试了几步。"""

import json
import sys
from collections import Counter
from pathlib import Path

guard_dir = Path(sys.argv[1])
undef_dir = Path(sys.argv[2])

undef = {}
for path in undef_dir.glob("*.json"):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if not data.get("error"):
        undef[path.name] = bool(data["utility"])

buckets = Counter()
samples = []
for path in sorted(guard_dir.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error") or data["utility"]:
        continue
    if not undef.get(path.name):
        continue                      # 只统计"无防御能过、守卫却挂"的对
    steps = (data.get("guard") or {}).get("steps") or []
    denied_at = [i for i, s in enumerate(steps) if not s["allowed"]]
    if not denied_at:
        buckets["失败但没有拦截"] += 1
        continue
    after = len(steps) - denied_at[0] - 1
    buckets[f"被拦后还试了 {min(after, 3)} 步" if after < 3 else "被拦后还试了 3+ 步"] += 1
    if len(samples) < 4 and after == 0:
        samples.append((path.name, steps[denied_at[0]]["action"][:70]))

total = sum(buckets.values())
print(f"守卫弄挂且无防御能过的对：{total}")
for key, value in sorted(buckets.items()):
    print(f"  {key}: {value}")
print("\n被拦后立即收尾的样例：")
for name, action in samples:
    print(f"  {name}: 被拦动作 {action}")
