"""下载便携版 MinGit（免安装），用于在没有 git 的机器上做仓库操作。"""

import json
import urllib.request
import zipfile
from pathlib import Path

DEPS = Path(r"D:\EAG-GUARD\.deps")
DEPS.mkdir(parents=True, exist_ok=True)


def fetch(url: str, dest: Path | None = None):
    req = urllib.request.Request(url, headers={"User-Agent": "dsh"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    if dest is None:
        return json.loads(data)
    dest.write_bytes(data)
    return None


release = fetch("https://api.github.com/repos/git-for-windows/git/releases/latest")
asset = next(a for a in release["assets"] if a["name"].startswith("MinGit-") and a["name"].endswith("-64-bit.zip"))
print("版本:", release["tag_name"], "| 文件:", asset["name"], f"{asset['size']/1e6:.1f} MB")

zip_path = DEPS / asset["name"]
if not zip_path.exists():
    fetch(asset["browser_download_url"], zip_path)
print("已下载:", zip_path)

out = DEPS / "mingit"
if out.exists():
    import shutil

    shutil.rmtree(out)
out.mkdir(parents=True)
with zipfile.ZipFile(zip_path) as zf:
    zf.extractall(out)
print("已解压:", out)
print("git.exe 存在:", (out / "cmd" / "git.exe").exists())
