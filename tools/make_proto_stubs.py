"""google.protobuf / proto.marshal 桩：google_llm 只在 import 期用到这些类型。"""

from pathlib import Path

ROOT = Path(r"D:\EAG-GUARD\.deps\ipi_stubs")

FILES = {
    "google/__init__.py": (
        '"""桩：仅为 google.protobuf 提供命名空间。"""\n'
        "import pkgutil\n\n"
        "__path__ = pkgutil.extend_path(__path__, __name__)\n"
    ),
    "google/protobuf/__init__.py": '"""桩。"""\n',
    "google/protobuf/struct_pb2.py": (
        '"""桩：只提供 Struct 类型名。"""\n\n\n'
        "class Struct(dict):\n"
        "    pass\n"
    ),
    "proto/__init__.py": '"""桩。"""\n',
    "proto/marshal/__init__.py": '"""桩。"""\n',
    "proto/marshal/collections/__init__.py": '"""桩。"""\n',
    "proto/marshal/collections/maps.py": (
        '"""桩。"""\n\n\n'
        "class MapComposite(dict):\n"
        "    pass\n"
    ),
    "proto/marshal/collections/repeated.py": (
        '"""桩。"""\n\n\n'
        "class RepeatedComposite(list):\n"
        "    pass\n"
    ),
}

for name, body in FILES.items():
    target = ROOT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    print("写出", name)
