"""答复复查：收尾前让模型自查"用户问的字段是否齐全"，缺的补齐。

依据（travel 全域失败分类）：
- 73% 的失败是"答复只含部分期望值"；
- 缺的字段依次是 名称 116、数字 60、地址 36、营业时间 12。
硬性模板试过，反而更差（0.429→0.400）——因为它是"事前要求"，模型照做率低。
这里改成"事后复查"：把用户原请求和当前答复一起给它，让它逐项核对并补全。
"""

from __future__ import annotations

from typing import Any

from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.types import ChatUserMessage, text_content_block_from_string

INSTRUCTION = """下面是一个任务的原始请求，以及你刚才给出的答复。

【原始请求】
{request}

【你的答复】
{answer}

请逐项核对：原始请求里要求你说出的**每一个字段**（名称、评分、地址、价格、
营业时间、日期、邮箱……），你的答复里是否都写了？数值与地址是否照抄了工具返回的原文？

- 有缺失就用你**已经查到过的信息**补全（不要编造、不要重新调用工具）；
- 已经齐全就原样返回。

只输出补全后的最终答复，不要解释你在做什么。"""


class AnswerReview(BasePipelineElement):
    """收尾前复查答复的完整性（只对配置了的域启用）。"""

    name = "answer_review"

    def __init__(self, llm: Any) -> None:
        self.llm = llm

    def query(self, query, runtime, env=None, messages=(), extra_args=None):
        extra_args = extra_args or {}
        if not messages or messages[-1].get("role") != "assistant":
            return query, runtime, env, messages, extra_args

        blocks = list(messages[-1].get("content") or [])
        answer = "\n".join(str(b.get("content") or "") for b in blocks if isinstance(b, dict))
        if not answer.strip():
            return query, runtime, env, messages, extra_args

        prompt = INSTRUCTION.format(request=query, answer=answer[:3000])
        try:
            _, _, _, out, _ = self.llm.query(
                prompt, runtime, env, [], extra_args
            )
        except Exception:          # 复查失败不影响原答复
            return query, runtime, env, messages, extra_args

        reply = ""
        for message in reversed(out):
            if message.get("role") == "assistant":
                reply = "\n".join(
                    str(b.get("content") or "")
                    for b in (message.get("content") or [])
                    if isinstance(b, dict)
                )
                break
        if not reply.strip() or reply.strip() == answer.strip():
            return query, runtime, env, messages, extra_args

        # 用更完整的版本替换最后一条消息
        new_message = dict(messages[-1])
        new_message["content"] = [{"type": "text", "text": reply, "content": reply}]
        return query, runtime, env, [*messages[:-1], new_message], extra_args
