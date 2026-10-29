"""守卫当副驾驶：拒绝时给出**具体的下一步**，而不只是"继续完成任务"。

诊断依据：travel 的守卫几乎不产生"效用提升"（+0.034，报告是 +0.379），
无防御基线两边又一样（0.259 vs 0.264）。说明问题不在"拦得对不对"，
而在拦完之后**没有把模型引向正确的动作**。

做法：拒绝时从授权范围里取出可用的信息，拼成一句具体的指引：
- 授权对象有哪些（O）；
- 允许的写操作有哪些（T 里的副作用工具）；
- 本次任务属于"查询"还是"办理"（依据 T 里有没有写工具）。
"""

from __future__ import annotations

from typing import Sequence

from .pipeline import StepRecord


def next_step_hint(scope, denied: Sequence[tuple[object, StepRecord]], tools: dict) -> str:
    """根据授权范围，给出一条可执行的下一步建议。"""
    lines: list[str] = []

    objects: list[str] = []
    for klass, values in sorted(scope.objects.items()):
        picked = sorted(str(v) for v in values)[:6]
        if picked:
            objects.append(f"{klass}: " + "、".join(picked))
    if objects:
        lines.append("本次授权的对象只有 —— " + "；".join(objects) + "。")
    else:
        lines.append("本次任务没有预先指定具体对象，对象由你按用户请求来选。")

    write_tools = sorted(
        name for name in scope.tools
        if name in tools and not tools[name].read_only
    )
    if write_tools:
        lines.append("允许的办理类工具：" + "、".join(write_tools) + "。")
    else:
        lines.append("本次**只允许查询**，不需要（也不允许）办理任何写操作；"
                     "查到信息后直接按要求答复即可。")

    if any(getattr(tools.get(getattr(call, "function", "")), "side_effect", False)
           for call, _rec in denied):
        lines.append("刚才被拒的是办理类动作：要么换成本次授权的对象，"
                     "要么这个任务本来就不需要办理——那就把查询结果说清楚。")
    return "\n".join("- " + line for line in lines)
