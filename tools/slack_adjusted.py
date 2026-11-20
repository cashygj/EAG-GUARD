"""剔除"注入污染标识符"的 20 对后，重算各臂的 slack 指标。"""

import json
from pathlib import Path

RUNS = Path(r"D:\EAG-GUARD\results\runs")
IMPOSSIBLE = {"user_task_7", "user_task_9", "user_task_10", "user_task_12"}

ARMS = [
    ("无防御（qwen-plus）", "slack_full_undefended"),
    ("EAG（qwen-plus）", "final_slack"),
    ("EAG（qwen3.5-27b）", "q35_slack_full"),
    ("IPIGuard（qwen-plus）", "ipi_official_slack_full"),
    ("IPIGuard（qwen3.5-27b）", "ipi_official_slack_full_q35"),
]

print(f"{'臂':26s} {'全部对':>14s} {'剔除后':>14s}")
for label, name in ARMS:
    run = RUNS / name
    if not run.exists():
        print(f"{label:26s}  （未跑）")
        continue
    stats = {}
    for path in run.glob("*.json"):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        stats[path.name] = data

    def summarize(items):
        n = len(items)
        if not n:
            return "—"
        asr = sum(1 for d in items if d["security"]) / n * 100
        ua = sum(1 for d in items if d["utility"]) / n * 100
        return f"{asr:5.1f}%/{ua:5.1f}%"

    all_items = list(stats.values())
    keep = [d for d in all_items if d["user_task"] not in IMPOSSIBLE]
    print(f"{label:26s} {summarize(all_items):>14s} {summarize(keep):>14s}")

print("\n（格式：ASR / UA；'剔除后'= 去掉 user_task_7/9/10/12 这 20 对）")
