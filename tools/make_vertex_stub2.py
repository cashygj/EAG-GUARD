"""补全 vertexai 桩：google_llm 在模块级用到了若干类型名。"""

from pathlib import Path

ROOT = Path(r"D:\EAG-GUARD\.deps\ipi_stubs")
vertexai = ROOT / "vertexai"
vertexai.mkdir(parents=True, exist_ok=True)

NAMES = [
    "Content", "FunctionCall", "FunctionDeclaration", "GenerationConfig",
    "GenerationResponse", "GenerativeModel", "Part", "Tool",
]

body = ['"""桩：IPIGuard 的 openai 路径不会用到 vertexai。"""', "", "",
        "def init(*args, **kwargs) -> None:", "    raise RuntimeError('vertexai 未安装（仅桩）')", "", ""]
for name in NAMES:
    body += [
        f"class {name}:",
        "    def __init__(self, *args, **kwargs) -> None:",
        f"        self.args = args  # {name} 桩",
        "",
    ]

(vertexai / "generative_models.py").write_text("\n".join(body), encoding="utf-8")
print("已补全 vertexai.generative_models：", ", ".join(NAMES))
