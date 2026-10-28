"""下载便携版 Git（连同正确的下载地址）。"""

import json
import time
import urllib.request
import zipfile
from pathlib import Path

DEPS = Path(r"D:\EAG-GUARD\.deps")
DEPS.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0"}


def get_json(url: str):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def download(url: str, dest: Path, label: str, limit=600) -> bool:
    start = time.time()
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as fh:
            while True:
                chunk = resp.read(256 * 1024)
                if not chunk:
                    break
                fh.write(chunk)
                if time.time() - start > limit:
                    raise TimeoutError("超时")
        size = dest.stat().st_size
        print(f"[成功] {label}: {size/1e6:.1f} MB / {time.time()-start:.0f}s", flush=True)
        return size > 5 * 1024 * 1024
    except Exception as exc:  # noqa: BLE001
        print(f"[失败] {label}: {type(exc).__name__} {str(exc)[:90]}", flush=True)
        if dest.exists():
            dest.unlink()
        return False


release = get_json("https://api.github.com/repos/git-for-windows/git/releases/latest")
tag = release["tag_name"]                    # 例如 v2.56.0.4.windows.1
asset = next(a for a in release["assets"]
             if a["name"].startswith("MinGit-") and a["name"].endswith("-64-bit.zip"))
name = asset["name"]
print("版本:", tag, "| 文件:", name, f"{asset['size']/1e6:.1f} MB", flush=True)

sources = [
    (asset["browser_download_url"], "GitHub 直连"),
    (f"https://ghfast.top/{asset['browser_download_url']}", "ghfast 代理"),
    (f"https://gh-proxy.com/{asset['browser_download_url']}", "gh-proxy 代理"),
]

zip_path = DEPS / name
for url, label in sources:
    print("尝试", label, "...", flush=True)
    if download(url, zip_path, label):
        break
else:
    print("全部源失败", flush=True)
    raise SystemExit(1)

out = DEPS / "mingit"
if out.exists():
    import shutil

    shutil.rmtree(out)
out.mkdir(parents=True)
with zipfile.ZipFile(zip_path) as zf:
    zf.extractall(out)
print("已解压:", out, "| git.exe:", (out / "cmd" / "git.exe").exists(), flush=True)
