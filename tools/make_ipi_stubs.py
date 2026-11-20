"""给 IPIGuard 官方实现的最小桩模块。

他们的 `agent_pipeline.py` 在模块级 import 了 anthropic / cohere / vertexai，
但我们只跑 openai 路径，这些客户端不会被调用——用空桩让 import 通过即可。
"""

from pathlib import Path

ROOT = Path(r"D:\EAG-GUARD\.deps\ipi_stubs")
ROOT.mkdir(parents=True, exist_ok=True)

STUBS = {
    "anthropic.py": (
        '"""桩：IPIGuard 的 openai 路径不会用到 anthropic。"""\n\n\n'
        "class Anthropic:\n"
        "    def __init__(self, *args, **kwargs) -> None:\n"
        "        raise RuntimeError('anthropic 未安装（仅桩）')\n\n\n"
        "class NOT_GIVEN:\n"
        "    pass\n"
    ),
    "cohere.py": (
        '"""桩：IPIGuard 的 openai 路径不会用到 cohere。"""\n\n\n'
        "class Client:\n"
        "    def __init__(self, *args, **kwargs) -> None:\n"
        "        raise RuntimeError('cohere 未安装（仅桩）')\n\n\n"
        "class ApiError(Exception):\n"
        "    pass\n"
    ),
    "vertexai.py": (
        '"""桩：IPIGuard 的 openai 路径不会用到 vertexai。"""\n\n\n'
        "def init(*args, **kwargs) -> None:\n"
        "    raise RuntimeError('vertexai 未安装（仅桩）')\n"
    ),
}

for name, body in STUBS.items():
    (ROOT / name).write_text(body, encoding="utf-8")
    print("写出", name)

print("目录:", ROOT)
