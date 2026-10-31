"""逐域算"守卫效应"（守卫 UA − 无防御 UA），与报告对齐，看差距落在哪个域。"""

import json
from pathlib import Path

RUNS = Path(r"D:\EAG-GUARD\results\runs")

GUARD = {
    "banking": "banking_v15_eag",
    "workspace": "workspace_v6_eag",
    "slack": "slack_full_eag",
    "travel": "travel_rv_eag",
}
UNDEF = {
    "banking": "banking_full_undefended",
    "workspace": "workspace_full_undefended",
    "slack": "slack_full_undefended",
    "travel": "travel_full_undefended",
}
# 报告表 4-1：无防御 ASR/UA → EAG ASR/UA
REPORT = {
    "banking": (0.6389, 0.7569, 0.0000, 0.7153),
    "workspace": (0.1708, 0.6333, 0.0000, 0.7708),
    "slack": (0.9429, 0.7238, 0.0190, 0.6667),
    "travel": (0.6214, 0.2643, 0.0143, 0.6429),
}


def read(run_name: str):
    path = RUNS / run_name / "summary.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    row = next(r for r in data["table"] if "按对" in str(r.get("域", "")))
    return data["pairs"], float(row["ASR"].rstrip("%")) / 100, float(row["UA"])


print(f"{'域':10s} {'无防御UA':>9s} {'守卫UA':>8s} {'我们的效应':>10s} {'报告的效应':>10s} {'差':>7s}")
tot = 0.0
for domain in GUARD:
    g = read(GUARD[domain])
    u = read(UNDEF[domain])
    if not g or not u:
        print(f"{domain}: 数据缺失")
        continue
    ours = g[2] - u[2]
    _, ru, _, rg = REPORT[domain]
    theirs = rg - ru
    print(f"{domain:10s} {u[2]:9.3f} {g[2]:8.3f} {ours:+10.3f} {theirs:+10.3f} {ours-theirs:+7.3f}")
    tot += (ours - theirs) * g[0] / 629

print(f"\n加权后：守卫效应差距对总 UA 的贡献 ≈ {tot:+.3f}")

