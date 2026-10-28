import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

#: 沙箱里系统临时目录不可用，测试统一用工作区内的固定目录。
WORK = ROOT / "tests" / ".work"


@pytest.fixture
def workdir() -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    return WORK
