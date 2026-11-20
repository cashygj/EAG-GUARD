"""matplotlib 桩：IPIGuard 只用它画 DAG 调试图，评测路径不调用。"""

from pathlib import Path

ROOT = Path(r"D:\EAG-GUARD\.deps\ipi_stubs")
pkg = ROOT / "matplotlib"
pkg.mkdir(parents=True, exist_ok=True)

(pkg / "__init__.py").write_text(
    '"""桩：评测路径不画图。"""\n\n'
    "def __getattr__(name):\n"
    "    def _noop(*args, **kwargs):\n"
    "        return None\n"
    "    return _noop\n",
    encoding="utf-8",
)

(pkg / "pylab.py").write_text(
    '"""桩：评测路径不画图。"""\n\n\n'
    "def __getattr__(name):\n"
    "    def _noop(*args, **kwargs):\n"
    "        return None\n"
    "    return _noop\n",
    encoding="utf-8",
)

print("matplotlib 桩已就绪：")
for path in sorted(pkg.iterdir()):
    print("   ", path.name)
