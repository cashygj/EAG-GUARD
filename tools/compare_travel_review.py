"""Recompute travel UA/ASR from saved pairs and compare exactly matched cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from repro_audit import read_run


def compare(old_path: Path, new_path: Path) -> dict:
    old_stats, old = read_run(old_path, 140)
    new_stats, new = read_run(new_path, 140)
    common = sorted(old.keys() & new.keys())
    fixed = [k for k in common if not old[k]["utility"] and new[k]["utility"]]
    broken = [k for k in common if old[k]["utility"] and not new[k]["utility"]]
    attack_fixed = [k for k in common if old[k]["security"] and not new[k]["security"]]
    attack_broken = [k for k in common if not old[k]["security"] and new[k]["security"]]
    per_user = []
    for user in sorted({k[1] for k in common}, key=lambda v: int(v.rsplit("_", 1)[1])):
        keys = [k for k in common if k[1] == user]
        before = sum(bool(old[k]["utility"]) for k in keys)
        after = sum(bool(new[k]["utility"]) for k in keys)
        per_user.append({"user_task": user, "matched": len(keys), "old_utility": before,
                         "new_utility": after, "net": after - before})
    before = sum(bool(old[k]["utility"]) for k in common)
    after = sum(bool(new[k]["utility"]) for k in common)
    return {
        "old_directory": str(old_path.resolve()), "new_directory": str(new_path.resolve()),
        "old": old_stats, "new": new_stats,
        "matched": {"n": len(common), "old_utility": before, "new_utility": after,
                    "old_ua": before / len(common) if common else None,
                    "new_ua": after / len(common) if common else None,
                    "ua_delta": (after - before) / len(common) if common else None,
                    "fixed": [list(k) for k in fixed], "broken": [list(k) for k in broken],
                    "attacks_fixed": [list(k) for k in attack_fixed],
                    "attacks_new": [list(k) for k in attack_broken]},
        "new_valid_without_old": [{"pair": list(k), "utility": new[k]["utility"],
                                   "security": new[k]["security"]} for k in sorted(new.keys() - old.keys())],
        "per_user": per_user,
        "limitations": [
            "One full run; observed growth does not establish repeat-run stability.",
            "Old run did not enforce temperature=0 in actual requests; new run does.",
            "Old attack-model label was not saved explicitly; new label is qwen-plus.",
            "The comparison measures the combined current implementation, not a single-component ablation.",
            "Runtime errors remain unknown; they are not automatically counted as safe or as utility failures.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", type=Path, default=Path("results/runs/final_travel"))
    parser.add_argument("--new", type=Path, default=Path("results/runs/review_travel_full_20261101"))
    parser.add_argument("--out", type=Path, default=Path("results/travel_full_comparison_20261101.json"))
    args = parser.parse_args()
    data = compare(args.old, args.new)
    args.out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"old": {k: data["old"][k] for k in ("valid", "utility_successes", "attack_successes", "ua_valid")},
                      "new": {k: data["new"][k] for k in ("valid", "utility_successes", "attack_successes", "ua_valid")},
                      "matched": {k: v for k, v in data["matched"].items() if k in ("n", "old_utility", "new_utility", "ua_delta")},
                      "fixed": len(data["matched"]["fixed"]), "broken": len(data["matched"]["broken"])},
                     ensure_ascii=False, indent=2))
    print(args.out)


if __name__ == "__main__":
    main()
