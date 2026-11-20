"""稳健下载 GitHub 仓库快照：流式落盘 + 重试 + 多 URL 回退。"""

import io
import shutil
import tarfile
import time
import urllib.request
import zipfile
from pathlib import Path

REPO = "Greysahy/ipiguard"
BRANCH = "main"
DEST = Path(r"D:\EAG-GUARD\.deps\ipiguard")
TMP = Path(r"D:\EAG-GUARD\_tmp")
TMP.mkdir(parents=True, exist_ok=True)

TAR_URL = f"https://codeload.github.com/{REPO}/tar.gz/refs/heads/{BRANCH}"
ZIP_URL = f"https://codeload.github.com/{REPO}/zip/refs/heads/{BRANCH}"


def download(url: str, target: Path, attempts: int = 5) -> bool:
    for index in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=300) as response:
                with target.open("wb") as handle:
                    shutil.copyfileobj(response, handle, length=1 << 16)
            size = target.stat().st_size
            if size > 100_000:
                print(f"  第 {index} 次成功：{size/1024/1024:.1f} MB")
                return True
            print(f"  第 {index} 次太小（{size} 字节），重试")
        except Exception as exc:                       # noqa: BLE001
            print(f"  第 {index} 次失败：{type(exc).__name__}: {str(exc)[:80]}")
        time.sleep(2 * index)
    return False


def extract(archive: Path) -> bool:
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as zf:
            top = zf.namelist()[0].split("/")[0]
            for name in zf.namelist():
                if not name.startswith(top + "/") or name.endswith("/"):
                    continue
                target = DEST / name[len(top) + 1:]
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(name) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
        return True

    with tarfile.open(archive, mode="r:gz") as tar:
        for member in tar.getmembers():
            parts = member.name.split("/", 1)
            if len(parts) < 2 or not parts[1] or not member.isfile():
                continue
            target = DEST / parts[1]
            target.parent.mkdir(parents=True, exist_ok=True)
            source = tar.extractfile(member)
            if source is None:
                continue
            with source, target.open("wb") as dst:
                shutil.copyfileobj(source, dst)
    return True


def main() -> int:
    if DEST.exists() and any(DEST.iterdir()):
        print("目录已存在，先清理:", DEST)
        shutil.rmtree(DEST, ignore_errors=True)
    DEST.mkdir(parents=True, exist_ok=True)

    for url, name in ((TAR_URL, "repo.tar.gz"), (ZIP_URL, "repo.zip")):
        archive = TMP / name
        print("尝试:", url)
        if download(url, archive):
            print("解压中…")
            if extract(archive):
                print("完成，顶层内容：")
                for path in sorted(DEST.iterdir())[:14]:
                    print("   ", path.name)
                return 0
    print("全部失败")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
