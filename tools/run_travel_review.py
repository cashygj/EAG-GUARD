"""Run all travel pairs in independent processes and verify complete coverage.

Uses the current script/config unchanged across workers. Successful traces are
never retried; runtime errors get at most two additional attempts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def read_records(directory: Path) -> list[dict]:
    records = []
    for path in directory.glob("*_user_task_*_injection_task_*.json"):
        records.append(json.loads(path.read_text(encoding="utf-8")))
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--parallelism", type=int, default=2)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--model", default="qwen-plus-2025-04-28")
    parser.add_argument("--attack-model-label", default="qwen-plus")
    args = parser.parse_args()
    if args.out.exists() and not args.resume:
        parser.error("Use a new output directory; historical results are preserved.")
    if not 1 <= args.workers <= 4:
        parser.error("workers must be between 1 and 4")
    if not 1 <= args.parallelism <= args.workers:
        parser.error("parallelism must be between 1 and workers")

    sys.path.insert(0, str(ROOT / ".venv" / "Lib" / "site-packages"))
    sys.path.insert(0, str(ROOT / "src"))
    from agentdojo.task_suite.load_suites import get_suite
    from eag_guard.bench.agentdojo_runner import PairRun, summarize_runs

    suite = get_suite("v1", "travel")
    users = list(suite.user_tasks)
    injections = list(suite.injection_tasks)
    expected = {(u, i) for u in users for i in injections}
    assert len(expected) == 140, f"Unexpected travel suite size: {len(expected)}"
    output = args.out.resolve()
    metadata_dir = output / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    jobs = []
    for index in range(args.workers):
        selected = users[index::args.workers]
        directory = output / "workers" / f"worker_{index}"
        argv = [str(ROOT / "scripts" / "run_bench.py"), "--suite", "travel", "--arm", "eag",
                "--user-tasks", ",".join(u.rsplit("_", 1)[1] for u in selected),
                "--injection-tasks", "all", "--model", args.model,
                "--attack-model-label", args.attack_model_label, "--calls", "15",
                "--feedback", "strong", "--no-cache", "--out", str(directory)]
        jobs.append({"index": index, "directory": directory, "argv": argv,
                     "expected": len(selected) * len(injections), "attempt": 0,
                     "done": False, "process": None})

    def launch(job):
        job["attempt"] += 1
        argv = job["argv"] + (["--resume"] if args.resume or job["attempt"] > 1 else [])
        bootstrap = ("import ssl,sys,runpy; sys.path.insert(0, "
                     + repr(str(ROOT / ".venv" / "Lib" / "site-packages"))
                     + "); sys.argv=" + repr(argv)
                     + "; runpy.run_path(sys.argv[0],run_name='__main__')")
        log = metadata_dir / f"worker_{job['index']}_{int(started)}_attempt_{job['attempt']}.log"
        job["log"] = log.open("wb")
        environment = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        job["process"] = subprocess.Popen(
            [sys.executable, "-u", "-c", bootstrap], cwd=ROOT, env=environment,
            stdout=job["log"], stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        job["done"] = False

    (metadata_dir / "orchestration.json").write_text(json.dumps({
        "model": args.model, "attack_model_label": args.attack_model_label,
        "workers": args.workers, "expected": len(expected), "no_cache": True,
        "parallelism": args.parallelism, "resume": args.resume,
        "request_temperature_enforced": True,
        "orchestrator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Running {len(jobs)} independent shards at parallelism={args.parallelism} for {len(expected)} travel pairs.", flush=True)
    next_report = 0
    while not all(job["done"] for job in jobs):
        for job in jobs:
            if job["done"] or job["process"] is None or job["process"].poll() is None:
                continue
            job["log"].close()
            records = read_records(job["directory"])
            needs_retry = len(records) < job["expected"] or any(r.get("error") for r in records)
            if needs_retry and job["attempt"] < 3:
                print(f"Worker {job['index']}: retrying incomplete/error pairs only.", flush=True)
                launch(job)
            else:
                job["done"] = True
        active = sum(job["process"] is not None and not job["done"]
                     and job["process"].poll() is None for job in jobs)
        for job in jobs:
            if active >= args.parallelism:
                break
            if job["process"] is None and not job["done"]:
                launch(job)
                active += 1
        if time.time() >= next_report:
            records = [r for job in jobs for r in read_records(job["directory"])]
            valid = [r for r in records if not r.get("error")]
            print(f"Progress: {len(records)}/140 saved, {len(valid)} valid, "
                  f"utility={sum(bool(r['utility']) for r in valid)}, "
                  f"attacks={sum(bool(r['security']) for r in valid)}, "
                  f"elapsed={time.time() - started:.0f}s", flush=True)
            next_report = time.time() + 30
        if not all(job["done"] for job in jobs):
            time.sleep(2)

    records = []
    manifests = []
    for job in jobs:
        manifests.append(json.loads((job["directory"] / "metadata" / "manifest.json").read_text(encoding="utf-8")))
        for path in job["directory"].glob("*_user_task_*_injection_task_*.json"):
            records.append(json.loads(path.read_text(encoding="utf-8")))
            shutil.copy2(path, output / path.name)
    reference = {k: v for k, v in manifests[0].items() if k != "pairs"}
    assert all({k: v for k, v in m.items() if k != "pairs"} == reference for m in manifests)
    keys = [(r["user_task"], r["injection_task"]) for r in records]
    assert len(keys) == len(set(keys)), "Duplicate pairs in worker outputs"
    assert set(keys) == expected, f"Missing/unexpected pairs: {expected ^ set(keys)}"
    (metadata_dir / "manifest.json").write_text(json.dumps({
        **reference, "pairs": [list(k) for k in sorted(expected)]},
        ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    runs = [PairRun(suite=r["suite"], user_task_id=r["user_task"],
                    injection_task_id=r["injection_task"], utility=r["utility"], security=r["security"],
                    executed=r.get("executed", []), final_answer=r.get("final_answer", ""),
                    error=r.get("error"), guard=r.get("guard")) for r in records]
    errors = [r.to_dict() for r in runs if r.error]
    summary = {**reference, "pairs": len(expected), "valid": len(runs) - len(errors),
               "table": summarize_runs(runs, suite).as_table(), "errors": errors,
               "duration_s": round(time.time() - started, 1), "workers": len(jobs),
               "cache": None, "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary["table"], ensure_ascii=False, indent=2), flush=True)
    print(f"Completed: valid={summary['valid']}/140, errors={len(errors)}, output={output}", flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
