"""Offline counterexamples and injection evidence; no model or network calls."""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agentdojo.agent_pipeline.ground_truth_pipeline import GroundTruthPipeline
from agentdojo.functions_runtime import FunctionsRuntime
from agentdojo.task_suite.load_suites import get_suite
from eag_guard.bench.agentdojo_runner import build_attack


def main():
    suite = get_suite("v1", "banking")
    task = suite.get_user_task_by_id("user_task_15")
    outcomes = {}
    for injection in suite.injection_tasks.values():
        utility, security = suite.run_task_with_pipeline(
            GroundTruthPipeline(task), task, injection, {})
        outcomes[injection.ID] = {"utility": utility, "security": security}
    attack = build_attack("important_instructions", suite,
                          SimpleNamespace(name="qwen-plus", model="qwen-plus"))
    bill_task = suite.get_user_task_by_id("user_task_0")
    injection = suite.get_injection_task_by_id("injection_task_0")
    injected = attack.attack(bill_task, injection)
    bills = {}
    for label, payload in (("clean", {}), ("injected", injected)):
        env = suite.load_and_inject_default_environment(payload)
        value, error = FunctionsRuntime(suite.tools).run_function(
            env, "read_file", {"file_path": "bill-december-2023.txt"})
        bills[label] = {"content": value, "error": error}
    result = {
        "task_15_prompt": task.PROMPT,
        "task_15_clean_ground_truth": outcomes,
        "limitations": [
            "Clean standard-solution replay tests logical predicate conflict only; it does not prove recoverability of erased evidence under attack.",
            "GroundTruthPipeline has oracle task knowledge; its utility must never be reported as model performance.",
        ],
        "predicate_sources": {i: inspect.getsource(suite.get_injection_task_by_id(i).security)
                              for i in ("injection_task_0", "injection_task_1", "injection_task_3", "injection_task_4")},
        "bill": bills,
    }
    out = ROOT / "results" / "benchmark_contract_probe.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(outcomes, ensure_ascii=False))
    print(out)


if __name__ == "__main__":
    main()
