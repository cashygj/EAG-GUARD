"""Audit saved pair traces without API calls; never infer outcomes from rounded tables."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = {
    "banking": ("banking_full_undefended", "final4_banking", 144),
    "workspace": ("workspace_full_undefended", "final5_workspace", 240),
    "slack": ("slack_full_undefended", "final_slack", 105),
    "travel": ("travel_full_undefended", "final_travel", 140),
}


def read_run(path: Path, expected: int) -> tuple[dict, dict]:
    meta_path = path / "summary.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    records = {}
    unreadable = []
    for file in sorted(path.glob("*_user_task_*_injection_task_*.json")):
        try:
            row = json.loads(file.read_text(encoding="utf-8"))
            key = (row["suite"], row["user_task"], row["injection_task"])
            if key in records:
                raise ValueError(f"duplicate pair: {key}")
            records[key] = row
        except (ValueError, KeyError) as exc:
            unreadable.append({"file": file.name, "error": str(exc)})
    valid = {key: row for key, row in records.items() if not row.get("error")}
    n = len(valid)
    utility = sum(bool(row["utility"]) for row in valid.values())
    security = sum(bool(row["security"]) for row in valid.values())
    unknown = max(0, expected - n)
    stats = {
        "run": path.name, "expected": expected, "found": len(records), "valid": n,
        "model": meta.get("model"), "code": meta.get("code"), "cache": meta.get("cache"),
        "utility_successes": utility, "attack_successes": security,
        "ua_valid": utility / n if n else None,
        "asr_valid": security / n if n else None,
        "ua_full_bounds": [utility / expected, (utility + unknown) / expected],
        "asr_full_bounds": [security / expected, (security + unknown) / expected],
        "errors": [{"pair": list(key), "error": row["error"]}
                   for key, row in records.items() if row.get("error")],
        "unreadable": unreadable,
        "security_positive_traces": [
            {"pair": list(key), "utility": row["utility"], "executed": row.get("executed", [])}
            for key, row in valid.items() if row["security"]
        ],
    }
    summary_row = next((r for r in meta.get("table", []) if r.get("域") == "合计（按对）"), None)
    stats["stored_summary"] = summary_row
    stats["summary_matches_traces"] = (
        summary_row is not None and summary_row.get("对数") == str(n)
        and summary_row.get("UA") == (f"{utility / n:.4f}" if n else "0.0000")
        and summary_row.get("ASR") == (f"{security / n * 100:.2f}%" if n else "0.00%")
    )
    return stats, valid


def audit(root: Path) -> dict:
    output = {"domains": {}, "limitations": [
        "Historical runs use different source fingerprints; paired deltas are descriptive, not isolated causal effects.",
        "Bounds treat missing/error outcomes as unknown. They are not confidence intervals.",
        "Tool-level ASR cannot be recovered from target-string presence in tool arguments.",
    ]}
    total = {"matched": 0, "undef_utility": 0, "eag_utility": 0,
             "utility_fixed": 0, "utility_broken": 0}
    for domain, (undef_name, eag_name, expected) in RUNS.items():
        undef_stats, undef = read_run(root / undef_name, expected)
        eag_stats, eag = read_run(root / eag_name, expected)
        common = sorted(undef.keys() & eag.keys())
        fixed = [list(k) for k in common if not undef[k]["utility"] and eag[k]["utility"]]
        broken = [list(k) for k in common if undef[k]["utility"] and not eag[k]["utility"]]
        u = sum(bool(undef[k]["utility"]) for k in common)
        g = sum(bool(eag[k]["utility"]) for k in common)
        output["domains"][domain] = {
            "undefended": undef_stats, "eag": eag_stats,
            "paired": {"matched": len(common), "undef_utility": u, "eag_utility": g,
                       "ua_delta": (g - u) / len(common) if common else None,
                       "fixed": fixed, "broken": broken,
                       "unmatched": [list(k) for k in sorted(undef.keys() ^ eag.keys())]},
        }
        for key, count in (("matched", len(common)), ("undef_utility", u),
                           ("eag_utility", g), ("utility_fixed", len(fixed)),
                           ("utility_broken", len(broken))):
            total[key] += count
    if total["matched"]:
        total["ua_delta"] = (total["eag_utility"] - total["undef_utility"]) / total["matched"]
    output["paired_total"] = total
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=ROOT / "results" / "runs")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "repro_audit.json")
    args = parser.parse_args()
    result = audit(args.runs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for domain, row in result["domains"].items():
        u, g, p = row["undefended"], row["eag"], row["paired"]
        print(f"{domain}: valid={u['valid']}/{u['expected']} -> {g['valid']}/{g['expected']}; "
              f"matched={p['matched']}; fixed={len(p['fixed'])}; broken={len(p['broken'])}")
    print(json.dumps(result["paired_total"], ensure_ascii=False))
    print(args.out)


if __name__ == "__main__":
    main()
