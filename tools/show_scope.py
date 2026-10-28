import json
import sys
from pathlib import Path

# 从一次真实轨迹里取出"授权范围推导"的结果，证明它是 T/O/P 三元组
run = Path(r"D:\EAG-GUARD\results\runs\strict_banking")
path = sorted(run.glob("banking_user_task_0_injection_task_1.json"))[0]
data = json.loads(path.read_text(encoding="utf-8"))
guard = data["guard"]
print("用户请求：", guard["request"])
print()
print("推导出的授权范围 A=(T,O,P)：")
print(guard["scope"])
