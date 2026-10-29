"""travel 失败细分：预订单是否已经完成？"""

import json
from pathlib import Path

run = Path(r"D:\EAG-GUARD\results\runs\travel_v3_eag")
buckets = {"成功": 0, "失败·已预订": 0, "失败·未预订": 0, "失败·零调用": 0}
for path in sorted(run.glob("*.json")):
    if path.name == "summary.json":
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error"):
        continue
    calls = data.get("executed") or []
    reserved = any(c["function"] in {"reserve_hotel", "reserve_restaurant", "reserve_car_rental"}
                   for c in calls)
    if data["utility"]:
        buckets["成功"] += 1
    elif not calls:
        buckets["失败·零调用"] += 1
    elif reserved:
        buckets["失败·已预订"] += 1
    else:
        buckets["失败·未预订"] += 1

total = sum(buckets.values())
for key, value in buckets.items():
    print(f"{key:12s} {value:4d}  ({value/total:.0%})")
print(f"{'合计':12s} {total:4d}")
