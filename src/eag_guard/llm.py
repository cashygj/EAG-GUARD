"""OpenAI 兼容的对话客户端。

刻意只用标准库：核心链路不引入任何第三方依赖，qwen-plus 走 DashScope 的
OpenAI 兼容端点即可。三种包装：

    ChatClient        直连
    CachedClient      按内容哈希落盘，重跑时优先读盘（省钱、可复现）
    ScriptedClient    测试用的假模型，按队列返回

`LLMJudge`、`LLMScopeParser`、规划器都只依赖 `complete(messages) -> str` 这个签名。
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"

Message = Mapping[str, str]


class LLMError(RuntimeError):
    pass


class Completer(Protocol):
    def complete(self, messages: Sequence[Message], **overrides: Any) -> str: ...


# --------------------------------------------------------------------------- 直连


@dataclass
class ChatClient:
    api_key: str
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    temperature: float = 0.0
    timeout: float = 90.0
    max_retries: int = 3
    _sleep: Callable[[float], None] = field(default=time.sleep, repr=False)

    def complete(self, messages: Sequence[Message] | str, **overrides: Any) -> str:
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        payload = {
            "model": overrides.get("model", self.model),
            "messages": [dict(m) for m in messages],
            "temperature": overrides.get("temperature", self.temperature),
        }
        if "max_tokens" in overrides:
            payload["max_tokens"] = overrides["max_tokens"]
        if "response_format" in overrides:
            payload["response_format"] = overrides["response_format"]

        url = self.base_url.rstrip("/") + "/chat/completions"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        last: Exception | None = None
        for attempt in range(self.max_retries):
            request = urllib.request.Request(
                url, data=body,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {self.api_key}"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as exc:
                last = exc
                if exc.code in (429, 500, 502, 503, 504) and attempt + 1 < self.max_retries:
                    self._sleep(2 ** attempt + random.random())
                    continue
                detail = exc.read().decode("utf-8", "replace")[:400]
                raise LLMError(f"HTTP {exc.code}: {detail}") from exc
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
                last = exc
                if attempt + 1 < self.max_retries:
                    self._sleep(2 ** attempt + random.random())
                    continue
                raise LLMError(f"调用失败：{exc}") from exc
        raise LLMError(f"调用失败：{last}")


# --------------------------------------------------------------------------- 缓存


class CachedClient:
    """把 (model, messages, temperature) 哈希成文件名，命中就直接返回。"""

    def __init__(self, inner: Completer, directory: str | Path) -> None:
        self.inner = inner
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.misses = 0

    def _key(self, messages: Sequence[Message], overrides: Mapping[str, Any]) -> str:
        payload = json.dumps({"messages": [dict(m) for m in messages],
                              "overrides": dict(overrides)}, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]

    def complete(self, messages: Sequence[Message], **overrides: Any) -> str:
        path = self.directory / f"{self._key(messages, overrides)}.json"
        if path.exists():
            self.hits += 1
            return json.loads(path.read_text(encoding="utf-8"))["content"]
        self.misses += 1
        content = self.inner.complete(messages, **overrides)
        path.write_text(json.dumps({"content": content}, ensure_ascii=False), encoding="utf-8")
        return content


# --------------------------------------------------------------------------- 假模型


class ScriptedClient:
    """按队列返回预设回复；队列空了就返回最后一条。"""

    def __init__(self, replies: Sequence[str]) -> None:
        self.replies = list(replies)
        self.calls: list[list[dict]] = []

    def complete(self, messages: Sequence[Message], **overrides: Any) -> str:
        self.calls.append([dict(m) for m in messages])
        if not self.replies:
            raise LLMError("ScriptedClient 没有可用回复")
        return self.replies.pop(0)


# --------------------------------------------------------------------------- 环境


def parse_dotenv(path: str | Path) -> dict[str, str]:
    """极简 .env 解析：KEY=VALUE，忽略注释与空行。

    用 utf-8-sig 读，兼容 Windows PowerShell 5.1 写出的带 BOM 文件。
    """
    out: dict[str, str] = {}
    text = Path(path).read_text(encoding="utf-8-sig")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def client_from_env(dotenv: str | Path = ".env", **kwargs: Any) -> ChatClient:
    """从 process env 或 .env 取 key；两者都没有就明确报错。"""
    key = os.environ.get("DASHSCOPE_API_KEY")
    model = os.environ.get("EAG_MODEL", DEFAULT_MODEL)
    base_url = os.environ.get("EAG_BASE_URL", DEFAULT_BASE_URL)
    path = Path(dotenv)
    if not key and path.exists():
        values = parse_dotenv(path)
        key = values.get("DASHSCOPE_API_KEY")
        model = values.get("EAG_MODEL", model)
        base_url = values.get("EAG_BASE_URL", base_url)
    if not key:
        raise LLMError(
            f"没有找到 DASHSCOPE_API_KEY。请在环境变量里设置，或写进 {path}（已 gitignore）。"
        )
    return ChatClient(api_key=key, model=model, base_url=base_url, **kwargs)
