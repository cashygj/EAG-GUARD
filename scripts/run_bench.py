#!/usr/bin/env python
"""在 AgentDojo 上跑 EAG-Guard（需要 DASHSCOPE_API_KEY）。

用法示例：

    # 单对冒烟：workspace 的 user_task_0 × injection_task_0
    python scripts/run_bench.py --suite workspace --user-tasks 0 --injection-tasks 0

    # 25 对切片：user_task_0-4 × injection_task_1-5
    python scripts/run_bench.py --suite slack --user-tasks 0-4 --injection-tasks 1-5

    # 对照臂
    python scripts/run_bench.py --suite banking --arm undefended
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eag_guard.bench.agentdojo_runner import (  # noqa: E402
    PairRun,
    build_attack,
    make_pipeline,
    run_pairs,
    summarize_runs,
)
from eag_guard.llm import LLMError, client_from_env  # noqa: E402
from eag_guard.bench.reproducibility import ensure_manifest  # noqa: E402


def code_fingerprint() -> str:
    """该构建的源码指纹。写进每次运行的元数据，避免再出现"这批数是哪个版本跑的"。"""
    import hashlib

    digest = hashlib.sha256()
    for path in sorted((ROOT / "src" / "eag_guard").rglob("*.py")):
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def run_clean(suite, pipeline, args, out_dir: Path) -> int:
    """不注入的干净基线：只回答"这个模型本来能做对多少"。"""
    user_ids = (list(suite.user_tasks) if args.user_tasks == "all"
                else parse_ids(args.user_tasks, "user_task"))
    print(f"\n{args.suite} · {args.arm} · 干净基线 {len(user_ids)} 个用户任务 → {out_dir}")

    runs: list[PairRun] = []
    started = time.time()
    for user_id in user_ids:
        task = suite.get_user_task_by_id(user_id)
        run = PairRun(suite=suite.name, user_task_id=user_id, injection_task_id="none")
        try:
            utility, _ = suite.run_task_with_pipeline(pipeline, task, None, {})
            run.utility = bool(utility)
            run.final_answer = pipeline.final_answer()
        except Exception as exc:
            run.error = f"{type(exc).__name__}: {exc}"
        run.executed = list(getattr(pipeline.executor, "executed", []))
        if hasattr(pipeline.executor, "to_dict"):
            run.guard = pipeline.executor.to_dict()
        runs.append(run)
        print(f"  {user_id}: {'完成' if run.utility else '未完成'}"
              + (f"  [{run.error}]" if run.error else ""))
        (out_dir / f"{suite.name}_{user_id}_clean.json").write_text(
            json.dumps(run.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    valid = [r for r in runs if not r.error]
    done = sum(1 for r in valid if r.utility)
    duration = time.time() - started
    ua = done / len(valid) if valid else 0.0
    print(f"\n干净基线 UA = {done}/{len(valid)} = {ua:.4f}"
          f"（失败 {len(runs) - len(valid)} 个，不计入）  耗时 {duration:.1f}s")

    (out_dir / "summary.json").write_text(json.dumps({
        "model": pipeline.model, "suite": args.suite, "arm": args.arm,
        "mode": "clean", "calls": args.calls, "tasks": len(user_ids),
        "valid": len(valid), "utility": done, "ua": round(ua, 4),
        "cache": pipeline.cache_stats, "duration_s": round(duration, 1),
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def parse_ids(text: str, prefix: str) -> list[str]:
    """"0-4,7" -> ['0','1','2','3','4','7']，再拼成 user_task_0 这样的 id。"""
    ids: list[int] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, _, end = part.partition("-")
            ids.extend(range(int(start), int(end) + 1))
        else:
            ids.append(int(part))
    return [f"{prefix}_{i}" for i in ids]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True,
                        choices=["workspace", "travel", "banking", "slack"])
    parser.add_argument("--user-tasks", default="0", help="如 0 或 0-4")
    parser.add_argument("--injection-tasks", default="0", help="如 0 或 1-5")
    parser.add_argument("--arm", default="eag", choices=["eag", "undefended"])
    parser.add_argument("--attack", default="important_instructions")
    parser.add_argument("--judge", default="llm", choices=["llm", "rule", "none"],
                        help="none = 关掉语义裁判（消融用）")
    parser.add_argument("--no-audit", action="store_true",
                        help="关掉输出审核（诊断用）")
    parser.add_argument("--structure-only", action="store_true",
                        help="纯结构白名单模式（消融: 报告表 4-2 的纯结构）")
    parser.add_argument("--pairs-file", type=Path, default=None,
                        help="只跑清单里的对（回归集），格式 {域: [{user_task, injection_task}]}")
    parser.add_argument("--no-delegation", action="store_true",
                        help="不承认委托边（消融: 纯结构）")
    parser.add_argument("--no-fpr", action="store_true", help="关掉字段级溯源（消融用）")
    parser.add_argument("--feedback", default="strong", choices=["weak", "strong"],
                        help="拒绝后的反馈强弱（报告里弱反馈效用更高）")
    parser.add_argument("--model", default=None, help="默认取 EAG_MODEL / qwen-plus")
    parser.add_argument("--attack-model-label", default=None,
                        help="攻击模板里的模型称呼；两臂必须相同，默认使用 --model 的值")
    parser.add_argument("--no-cache", action="store_true",
                        help="不落盘缓存（默认缓存在 results/cache/agent）")
    parser.add_argument("--calls", type=int, default=15, help="循环上限轮数")
    parser.add_argument("--no-injection", action="store_true",
                        help="干净基线：不注入，只测用户任务效用")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--force", action="store_true", help="覆盖已有输出目录")
    parser.add_argument("--resume", action="store_true",
                        help="复用已完成的轨迹，只跑缺失或失败的对")
    args = parser.parse_args()

    try:
        client = client_from_env(ROOT / ".env")
    except LLMError as exc:
        print(f"[FAIL] {exc}")
        return 2
    model = args.model or client.model
    print(f"model={model}  base_url={client.base_url}")

    from agentdojo.attacks.attack_registry import ATTACKS
    from agentdojo.task_suite.load_suites import get_suite

    suite = get_suite("v1", args.suite)
    cache_dir = None if args.no_cache else (ROOT / "results" / "cache" / "agent")
    from eag_guard.pipeline import GuardConfig

    pipeline = make_pipeline(suite, client, args.arm, calls=args.calls,
                             judge=args.judge, model=model, cache_dir=cache_dir,
                             config=GuardConfig(
                                 feedback=args.feedback,
                                 allow_delegation=not args.no_delegation,
                                 structure_only=args.structure_only,
                                 output_audit=not args.no_audit,
                                 enable_judge=args.judge != "none",
                                 enable_fpr=not args.no_fpr,
                             ))
    attack = build_attack(args.attack, suite, pipeline, model_label=args.attack_model_label)

    user_ids = (list(suite.user_tasks) if args.user_tasks == "all"
                else parse_ids(args.user_tasks, "user_task"))
    injection_ids = (list(suite.injection_tasks) if args.injection_tasks == "all"
                     else parse_ids(args.injection_tasks, "injection_task"))
    if args.pairs_file is not None:
        # 回归集：只跑清单里指定的对，省时省钱。
        manifest = json.loads(args.pairs_file.read_text(encoding="utf-8"))
        entries = manifest.get(args.suite) or []
        if not entries:
            print(f"[FAIL] {args.pairs_file} 里没有 {args.suite} 的对")
            return 2
        pairs = [(e["user_task"], e["injection_task"]) for e in entries]
    else:
        pairs = [(u, i) for u in user_ids for i in injection_ids]
    for user_id, injection_id in pairs:
        if user_id not in suite.user_tasks:
            print(f"[FAIL] 没有 {user_id}")
            return 2
        if not args.no_injection and injection_id not in suite.injection_tasks:
            print(f"[FAIL] 没有 {injection_id}")
            return 2

    out_dir = args.out or (ROOT / "results" / "runs" /
                           f"{args.suite}_{args.arm}_{time.strftime('%Y%m%d-%H%M%S')}")
    if out_dir.exists() and not (args.force or args.resume):
        print(f"[FAIL] {out_dir} 已存在；加 --force 覆盖，或加 --resume 续跑")
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save before the first model call, so interruption does not erase the
    # experiment identity. Legacy traces cannot silently join a new build.
    import hashlib
    import importlib.metadata
    import agentdojo

    benchmark_hash = hashlib.sha256()
    benchmark_root = Path(agentdojo.__file__).parent
    for path in sorted(benchmark_root.rglob("*")):
        if path.is_file() and path.suffix in {".py", ".yaml", ".yml", ".json", ".txt"}:
            benchmark_hash.update(path.relative_to(benchmark_root).as_posix().encode())
            benchmark_hash.update(path.read_bytes())
    manifest = {
        "schema": 1, "code": code_fingerprint(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "agentdojo_version": importlib.metadata.version("agentdojo"),
        "benchmark_sha256": benchmark_hash.hexdigest(), "benchmark_version": "v1",
        "model": model, "temperature": 0.0, "base_url": client.base_url,
        "request_temperature_enforced": True,
        "suite": args.suite, "arm": args.arm, "attack": args.attack,
        "attack_model_label": args.attack_model_label or model,
        "calls": args.calls, "judge": args.judge, "feedback": args.feedback,
        "no_delegation": args.no_delegation, "structure_only": args.structure_only,
        "no_audit": args.no_audit, "no_fpr": args.no_fpr,
        "no_cache": args.no_cache, "no_injection": args.no_injection,
        "pairs": [list(pair) for pair in pairs],
    }
    try:
        ensure_manifest(out_dir, manifest, resume=args.resume)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}")
        return 2

    if args.no_injection:
        return run_clean(suite, pipeline, args, out_dir)

    print(f"\n{args.suite} · {args.arm} · {len(pairs)} 对 → {out_dir}")

    def report(run) -> None:
        mark = "被攻破" if run.security else "安全"
        util = "完成" if run.utility else "未完成"
        extra = f"  [{run.error}]" if run.error else ""
        print(f"  {run.user_task_id} × {run.injection_task_id}: {mark} / {util}{extra}")

    started = time.time()
    runs = run_pairs(suite, pairs, pipeline, attack, out_dir=out_dir,
                     on_result=report, resume=args.resume)

    summary = summarize_runs(runs, suite)
    table = summary.as_table()
    header = ["域", "对数", "ASR", "UA", "工具级ASR"]
    widths = [max(len(str(r[k])) for r in table + [dict(zip(header, header))]) for k in header]
    print("\n" + "  ".join(h.ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in table:
        print("  ".join(str(row[k]).ljust(w) for k, w in zip(header, widths)))

    errors = [r for r in runs if r.error]
    duration = time.time() - started
    counted = len(runs) - len(errors)
    print(f"\n耗时 {duration:.1f}s，轨迹写在 {out_dir}，"
          f"失败 {len(errors)} 对（不计入指标，有效 {counted} 对）")
    meta = {
        "code": code_fingerprint(),
        "model": model,
        "scope_model": model,
        "judge_model": model if args.judge == "llm" else None,
        "temperature": 0.0,
        "request_temperature_enforced": True,
        "api_model_field": model,
        "base_url": client.base_url,
        "suite": args.suite,
        "arm": args.arm,
        "attack": args.attack,
        "attack_model_label": args.attack_model_label or model,
        "judge": args.judge,
        "feedback": args.feedback,
        "calls": args.calls,
        "pairs": len(pairs),
        "cache": pipeline.cache_stats,
        "duration_s": round(duration, 1),
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "table": table,
        "errors": [r.to_dict() for r in errors],
    }
    (out_dir / "summary.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())





