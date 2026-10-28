import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from eag_guard.integrations.agentdojo import EAGGuardElement

values = ["'External_", '"External_"', "External_", " external_ ", "External"]
for v in values:
    print(repr(v), "->", repr(EAGGuardElement._cosmetic(v)))
