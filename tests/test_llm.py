"""模型客户端：请求构造、重试、缓存、.env 读取。"""

import json
import urllib.error
import uuid

import pytest

from eag_guard.llm import (
    CachedClient,
    ChatClient,
    LLMError,
    ScriptedClient,
    client_from_env,
    parse_dotenv,
)


class _Resp:
    def __init__(self, content: str) -> None:
        self._body = json.dumps({"choices": [{"message": {"content": content}}]}).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self._body


def test_request_is_openai_compatible(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["auth"] = request.get_header("Authorization")
        return _Resp("你好")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = ChatClient(api_key="sk-test", model="qwen-plus")
    assert client.complete([{"role": "user", "content": "hi"}]) == "你好"
    assert captured["url"].endswith("/chat/completions")
    assert captured["body"]["model"] == "qwen-plus"
    assert captured["body"]["temperature"] == 0.0
    assert captured["auth"] == "Bearer sk-test"


def test_retries_then_succeeds(monkeypatch) -> None:
    state = {"n": 0}

    def fake_urlopen(request, timeout):
        state["n"] += 1
        if state["n"] < 3:
            raise urllib.error.HTTPError(request.full_url, 429, "rate limited", None, None)
        return _Resp("ok")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = ChatClient(api_key="k", _sleep=lambda _s: None)
    assert client.complete([{"role": "user", "content": "hi"}]) == "ok"
    assert state["n"] == 3


def test_gives_up_after_retries(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 503, "down", None, None)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = ChatClient(api_key="k", max_retries=2, _sleep=lambda _s: None)
    with pytest.raises(LLMError):
        client.complete([{"role": "user", "content": "hi"}])


def test_cache_hits_disk(workdir) -> None:
    state = {"n": 0}

    class Inner:
        def complete(self, messages, **overrides):
            state["n"] += 1
            return f"answer-{state['n']}"

    cached = CachedClient(Inner(), workdir / "cache" / uuid.uuid4().hex)
    messages = [{"role": "user", "content": "same"}]
    assert cached.complete(messages) == "answer-1"
    assert cached.complete(messages) == "answer-1"   # 命中缓存
    assert state["n"] == 1
    assert cached.hits == 1


def test_parse_dotenv(workdir) -> None:
    path = workdir / "sample.env"
    path.write_text("# comment\nDASHSCOPE_API_KEY=sk-abc\nEAG_MODEL='qwen-max'\n\n", encoding="utf-8")
    values = parse_dotenv(path)
    assert values["DASHSCOPE_API_KEY"] == "sk-abc"
    assert values["EAG_MODEL"] == "qwen-max"


def test_parse_dotenv_handles_bom(workdir) -> None:
    """PowerShell 5.1 的 utf8 会写 BOM，不能把 key 名污染成 \\ufeffDASHSCOPE_API_KEY。"""
    path = workdir / "bom.env"
    path.write_text("DASHSCOPE_API_KEY=sk-bom\n", encoding="utf-8-sig")
    assert parse_dotenv(path)["DASHSCOPE_API_KEY"] == "sk-bom"


def test_client_from_env_reads_dotenv(workdir, monkeypatch) -> None:
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    path = workdir / "with-key.env"
    path.write_text("DASHSCOPE_API_KEY=sk-from-file\n", encoding="utf-8")
    client = client_from_env(path)
    assert client.api_key == "sk-from-file"


def test_client_from_env_without_key_raises(workdir, monkeypatch) -> None:
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    with pytest.raises(LLMError):
        client_from_env(workdir / "missing.env")


def test_scripted_client_pops_queue() -> None:
    client = ScriptedClient(["a", "b"])
    assert client.complete([]) == "a"
    assert client.complete([]) == "b"
    with pytest.raises(LLMError):
        client.complete([])
