"""回归集跑批：只跑 results/regression_set.json 里的对，并与上一次结果对比。

    python tools/regress.py                 # 跑一遍并对比
    python tools/regress.py --baseline DIR  # 指定对比基线目录

每个域只跑 8 对（共 32 对，约 10 分钟），用来在改代码后快速判断
"有没有修好已知失败、有没有弄坏已知通过"。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\EAG-GUARD")
RUNS = ROOT / "results" / "runs"
MANIFEST = ROOT / "results" / "regression_set.json"
PY = ROOT / ".venv" / "Scripts" / "python.exe"
BENCH = ROOT / "scripts" / "run_bench.py"
MODEL = "qwen-plus-2025-04-28"

BASELINES = {
    "travel": "travel_rv_eag",
    "workspace": "workspace_v6_eag",
    "slack": "slack_full_eag",
    "banking": "banking_v15_eag",
}


def load(run: Path) -> dict[str, bool]:
    out = {}
    for path in run.glob("*.json"):
        if path.name == "summary.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("error"):
            continue
        out[f'{data["user_task"]}|{data["injection_task"]}'] = bool(data["utility"])
    return out


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    summary = {}
    for domain, pairs in manifest.items():
        out_dir = RUNS / f"reg_{domain}"
        if out_dir.exists():
            shutil.rmtree(out_dir)          # 每次清空，避免旧样本污染统计
        print(f"\n===== {domain}（{len(pairs)} 对）")
        cmd = [str(PY), str(BENCH), "--suite", domain, "--arm", "eag",
               "--model", MODEL, "--pairs-file", str(MANIFEST),
               "--out", str(out_dir)]
        subprocess.run(cmd, cwd=ROOT, check=False)
        now = load(out_dir)
        base = load(RUNS / BASELINES.get(domain, "")) if BASELINES.get(domain) else {}
        fixed = [k for k, v in now.items() if v and base.get(k) is False]
        broken = [k for k, v in now.items() if not v and base.get(k) is True]
        summary[domain] = {"now": sum(now.values()), "total": len(now),
                           "fixed": fixed, "broken": broken}

    print("\n===== 回归对比")
    for domain, info in summary.items():
        print(f"{domain:10s} 通过 {info['now']}/{info['total']}"
              f" | 修好 {len(info['fixed'])} | 弄坏 {len(info['broken'])}")
        for key in info["fixed"][:5]:
            print(f"    ✔ 修好 {key}")
        for key in info["broken"][:5]:
            print(f"    ✘ 弄坏 {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


