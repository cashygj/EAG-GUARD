"""把 IPIGuard 官方实现里"非 openai 路径"的重型 import 改成可选导入。

只改 import 段：anthropic / cohere / vertexai / 各自 LLM 与 transformers 检测器
在 IPIGuard(openai) 路径上永远不会被调用。IPIGuard 的算法、提示词、执行逻辑
一行不改。
"""

from pathlib import Path

path = Path(
    r"D:\EAG-GUARD\.deps\ipiguard\agentdojo\src\agentdojo\agent_pipeline\agent_pipeline.py"
)
text = path.read_text(encoding="utf-8")

if "[EAG-PATCH] optional imports" in text:
    print("已打过补丁，跳过")
    raise SystemExit(0)

old_head = """import anthropic
import cohere
import openai
import vertexai
import yaml
from pydantic import BaseModel, ConfigDict, model_validator
from typing_extensions import Self

from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.agent_pipeline.basic_elements import InitQuery, SystemMessage, ReActQuery
from agentdojo.agent_pipeline.llms.anthropic_llm import AnthropicLLM
from agentdojo.agent_pipeline.llms.cohere_llm import CohereLLM
from agentdojo.agent_pipeline.llms.google_llm import GoogleLLM
from agentdojo.agent_pipeline.llms.openai_llm import OpenAILLM, OpenAILLMToolFilter
from agentdojo.agent_pipeline.llms.react_llm import ReActOpenAILLM
from agentdojo.agent_pipeline.llms.prompting_llm import PromptingLLM
from agentdojo.agent_pipeline.llms.ipiguard_llm import OpenAIConstructLLM, OpenAITraverseLLM
from agentdojo.agent_pipeline.pi_detector import TransformersBasedPIDetector
"""

new_head = '''# [EAG-PATCH] optional imports —— 仅影响非 openai 分支，IPIGuard 逻辑不变
import openai
import yaml
from pydantic import BaseModel, ConfigDict, model_validator
from typing_extensions import Self

from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.agent_pipeline.basic_elements import InitQuery, SystemMessage, ReActQuery
from agentdojo.agent_pipeline.llms.openai_llm import OpenAILLM, OpenAILLMToolFilter
from agentdojo.agent_pipeline.llms.ipiguard_llm import OpenAIConstructLLM, OpenAITraverseLLM


def _optional(module: str, name: str):
    """尽力导入；缺依赖时返回 None（对应分支在 IPIGuard 路径上不会被调用）。"""
    try:
        imported = __import__(module, fromlist=[name])
        return getattr(imported, name, None)
    except Exception:                      # noqa: BLE001
        return None


anthropic = None
cohere = None
vertexai = None
AnthropicLLM = _optional("agentdojo.agent_pipeline.llms.anthropic_llm", "AnthropicLLM")
CohereLLM = _optional("agentdojo.agent_pipeline.llms.cohere_llm", "CohereLLM")
GoogleLLM = _optional("agentdojo.agent_pipeline.llms.google_llm", "GoogleLLM")
ReActOpenAILLM = _optional("agentdojo.agent_pipeline.llms.react_llm", "ReActOpenAILLM")
PromptingLLM = _optional("agentdojo.agent_pipeline.llms.prompting_llm", "PromptingLLM")
TransformersBasedPIDetector = _optional(
    "agentdojo.agent_pipeline.pi_detector", "TransformersBasedPIDetector"
)
'''

if old_head not in text:
    print("未匹配到 import 段，未改动")
    raise SystemExit(1)

path.write_text(text.replace(old_head, new_head, 1), encoding="utf-8")
print("已把重型 import 改为可选导入")
