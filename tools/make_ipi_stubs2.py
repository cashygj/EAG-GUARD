"""把桩模块补成包（vertexai 等需要子模块）。"""

from pathlib import Path

ROOT = Path(r"D:\EAG-GUARD\.deps\ipi_stubs")
ROOT.mkdir(parents=True, exist_ok=True)

# vertexai 需要作为包存在，并提供子模块
vertexai = ROOT / "vertexai"
vertexai.mkdir(exist_ok=True)
(vertexai / "__init__.py").write_text(
    '"""桩：IPIGuard 的 openai 路径不会用到 vertexai。"""\n\n\n'
    "def init(*args, **kwargs) -> None:\n"
    "    raise RuntimeError('vertexai 未安装（仅桩）')\n",
    encoding="utf-8",
)
(vertexai / "generative_models.py").write_text(
    '"""桩：仅供 import 通过。"""\n\n\n'
    "class GenerativeModel:\n"
    "    def __init__(self, *args, **kwargs) -> None:\n"
    "        raise RuntimeError('vertexai 未安装（仅桩）')\n\n\n"
    "class Part:\n"
    "    @staticmethod\n"
    "    def from_text(*args, **kwargs):\n"
    "        raise RuntimeError('vertexai 未安装（仅桩）')\n",
    encoding="utf-8",
)
# 旧的单文件桩要删掉，否则会遮蔽包
old = ROOT / "vertexai.py"
if old.exists():
    old.unlink()

print("vertexai 包已就绪：")
for path in sorted(vertexai.iterdir()):
    print("   ", path.name)
