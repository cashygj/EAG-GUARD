#!/usr/bin/env python
"""连通性自检：只发一条最小请求，确认 key 与端点可用。

不会打印 key，只打印模型名与回复内容。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eag_guard.llm import LLMError, client_from_env  # noqa: E402


def main() -> int:
    try:
        client = client_from_env(ROOT / ".env")
    except LLMError as exc:
        print(f"[FAIL] {exc}")
        return 2

    print(f"model   = {client.model}")
    print(f"base_url = {client.base_url}")
    print(f"key     = 已读到（长度 {len(client.api_key)}，不显示）")
    try:
        reply = client.complete(
            [{"role": "user", "content": "只回复两个字：连通"}],
            max_tokens=16,
        )
    except LLMError as exc:
        print(f"[FAIL] 调用失败：{exc}")
        return 1
    print(f"[OK] 回复 = {reply.strip()!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
