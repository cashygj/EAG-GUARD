"""汇总四域最新结果与报告差距（用指定运行目录）。"""

from pathlib import Path

import json

RUNS = Path(r"D:\EAG-GUARD\results\runs")

# 目前各域"最新且完整"的运行（注意：部分是今天修 bug 之前跑的）
LATEST = {
    "banking": "final3_banking",
    "workspace": "final_workspace",
    "slack": "final_slack",
    "travel": "final_travel",
}
REPORT = {
    "banking": (0.0000, 0.7153),
    "workspace": (0.0000, 0.7708),
    "slack": (0.0190, 0.6667),
    "travel": (0.0143, 0.6429),
}


def load(run_name: str):
    path = RUNS / run_name / "summary.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    row = next(r for r in data["table"] if "按对" in str(r.get("域", "")))
    return data["pairs"], float(row["ASR"].rstrip("%")) / 100, float(row["UA"])


print(f"{'域':10s} {'对数':>4s} {'我们ASR':>8s} {'我们UA':>7s} {'报告ASR':>8s} {'报告UA':>7s} {'UA差':>7s}")
tot_n = tot_ua = tot_asr = 0.0
rep_ua = rep_asr = 0.0
for domain, run_name in LATEST.items():
    loaded = load(run_name)
    if loaded is None:
        print(f"{domain:10s} 运行缺失：{run_name}")
        continue
    pairs, asr, ua = loaded
    r_asr, r_ua = REPORT[domain]
    print(f"{domain:10s} {pairs:4d} {asr*100:7.2f}% {ua:7.3f} {r_asr*100:7.2f}% {r_ua:7.3f} {ua-r_ua:+7.3f}")
    tot_n += pairs
    tot_ua += ua * pairs
    tot_asr += asr * pairs
    rep_ua += r_ua * pairs
    rep_asr += r_asr * pairs

print()
print(f"按对合计  我们：ASR {tot_asr/tot_n*100:.2f}%  UA {tot_ua/tot_n:.4f}")
print(f"按对合计  报告：ASR {rep_asr/tot_n*100:.2f}%  UA {rep_ua/tot_n:.4f}")
print(f"UA 缺口：{(rep_ua-tot_ua)/tot_n:.4f}")


