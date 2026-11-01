"""Refuse to resume traces produced under a different experiment contract."""

import json
from pathlib import Path


def ensure_manifest(directory: Path, manifest: dict, *, resume: bool = False) -> None:
    path = directory / "metadata" / "manifest.json"
    if resume:
        if path.exists():
            stored = json.loads(path.read_text(encoding="utf-8"))
            if stored != manifest:
                changed = sorted(k for k in stored.keys() | manifest.keys()
                                 if stored.get(k) != manifest.get(k))
                raise ValueError("实验配置发生变化，不能混合续跑：" + ", ".join(changed)
                                 + "；请使用新的 --out 目录")
        elif any(directory.glob("*_user_task_*.json")):
            raise ValueError("旧轨迹没有实验清单，无法验证续跑条件；请使用新的 --out 目录")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
                    encoding="utf-8")
