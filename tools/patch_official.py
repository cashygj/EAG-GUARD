from pathlib import Path

p = Path(r"D:\EAG-GUARD\tools\official_baseline.py")
t = p.read_text(encoding="utf-8")
t = t.replace(
    "from agentdojo.attacks.attack_registry import load_attack",
    "from eag_guard.bench.agentdojo_runner import build_attack",
)
t = t.replace(
    'attack = load_attack("important_instructions", suite, pipeline)',
    'attack = build_attack("important_instructions", suite, pipeline, model_label="qwen-plus")',
)
p.write_text(t, encoding="utf-8")
print("patched")
