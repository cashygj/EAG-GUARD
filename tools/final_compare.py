"""四域全量对照：qwen-plus / qwen3.5-27b / 报告。"""

import json
from pathlib import Path

RUNS = Path(r"D:\EAG-GUARD\results\runs")

ARMS = {
    "qwen-plus": {
        "banking": "final4_banking",
        "workspace": "final5_workspace",
        "slack": "final_slack",
        "travel": "final_travel",
    },
    "qwen3.5-27b": {
        "banking": "q35_banking_full",
        "workspace": "q35_workspace_full",
        "slack": "q35_slack_full",
        "travel": "q35_travel_full",
    },
}
REPORT = {
    "banking": (0.0000, 0.7153),
    "workspace": (0.0000, 0.7708),
    "slack": (0.0190, 0.6667),
    "travel": (0.0143, 0.6429),
}


def read(run_name: str):
    path = RUNS / run_name / "summary.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    row = next(r for r in data["table"] if "按对" in str(r.get("域", "")))
    return data["pairs"], float(row["ASR"].rstrip("%")) / 100, float(row["UA"])


for arm, runs in ARMS.items():
    print(f"\n===== {arm}")
    print(f"{'域':10s} {'对数':>4s} {'ASR':>7s} {'UA':>7s} {'报告UA':>7s} {'差':>7s}")
    n_sum = asr_sum = ua_sum = 0.0
    for domain, run_name in runs.items():
        loaded = read(run_name)
        if loaded is None:
            print(f"{domain:10s}  （未完成：{run_name}）")
            continue
        pairs, asr, ua = loaded
        r_asr, r_ua = REPORT[domain]
        print(f"{domain:10s} {pairs:4d} {asr*100:6.2f}% {ua:7.3f} {r_ua:7.3f} {ua-r_ua:+7.3f}")
        n_sum += pairs
        asr_sum += asr * pairs
        ua_sum += ua * pairs
    if n_sum:
        print(f"{'合计':10s} {n_sum:4.0f} {asr_sum/n_sum*100:6.2f}% {ua_sum/n_sum:7.4f} "
              f"{0.7122:7.3f} {ua_sum/n_sum-0.7122:+7.3f}")
