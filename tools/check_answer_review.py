"""验证答复复查元件确实替换了最后一条消息。"""

import sys
from types import SimpleNamespace

sys.path.insert(0, "D:/EAG-GUARD/src")
from eag_guard.bench.answer_review import AnswerReview


class FakeLLM:
    """收到复查提示后返回一份"补全版"答复。"""

    def __init__(self) -> None:
        self.calls = []

    def query(self, query, runtime, env=None, messages=(), extra_args=None):
        self.calls.append(query[:60])
        reply = {"role": "assistant",
                 "content": [{"type": "text", "content": "名称：X\n地址：123 Rue de la Gaite\n"}]}
        return query, runtime, env, [reply], extra_args or {}


llm = FakeLLM()
element = AnswerReview(llm)
messages = [{"role": "assistant",
             "content": [{"type": "text", "content": "我找到了 X"}]}]
_, _, _, out, _ = element.query("告诉我名称和地址", None, None, messages, {})
print("复查调用次数:", len(llm.calls))
print("返回消息:", out[-1]["content"][0].get("content"))
assert "123 Rue de la Gaite" in out[-1]["content"][0]["content"]
print("OK：答复被替换为补全版")
