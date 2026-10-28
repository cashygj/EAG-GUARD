"""用 GitHub REST API 把当前 git 索引里的文件推成一个提交。

为什么不用 git push：这台机器的沙箱里 schannel 拿不到凭据、MinGit 又没带
openssl 后端，git 的 HTTPS 完全用不了；而 Python 的 TLS 是通的，所以改走 API。

用法：
    python tools/push_via_api.py <owner/repo> <token> [分支] [提交信息]

安全性：token 只在本进程内存里，不写任何文件、不进 git config。
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(r"D:\EAG-GUARD")
GIT = REPO / ".deps" / "mingit" / "cmd" / "git.exe"
API = "https://api.github.com"


def call(method: str, path: str, token: str, payload: dict | None = None) -> dict:
    """调用一次 API；网络抖动时重试。"""
    import time

    last: Exception | None = None
    for attempt in range(4):
        try:
            return _call_once(method, path, token, payload)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            raise RuntimeError(f"{method} {path} -> {exc.code}: {detail}") from None
        except Exception as exc:  # noqa: BLE001  网络层抖动
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"{method} {path} 连续失败: {type(last).__name__} {last}")


def _call_once(method: str, path: str, token: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "eag-guard-push",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read()
        return json.loads(body) if body else {}


def tracked_files() -> list[str]:
    out = subprocess.run([str(GIT), "ls-files"], cwd=REPO, capture_output=True,
                         text=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        raise RuntimeError(out.stderr)
    return [line for line in out.stdout.splitlines() if line.strip()]


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    repo = sys.argv[1]
    token = sys.argv[2]
    branch = sys.argv[3] if len(sys.argv) > 3 else "main"
    message = sys.argv[4] if len(sys.argv) > 4 else "EAG-Guard 重建"

    # 空仓库不允许直接建 blob（409），先用 Contents API 放一个 README 初始化
    try:
        call("POST", f"/repos/{repo}/git/blobs", token, {"content": "e30=", "encoding": "base64"})
    except RuntimeError as exc:
        if "409" in str(exc):
            print("仓库为空，先初始化 README ...")
            call("PUT", f"/repos/{repo}/contents/README.md", token, {
                "message": "初始化仓库",
                "content": base64.b64encode("# EAG-Guard\n\n初始化占位，随后由脚本覆写。\n".encode()).decode(),
            })
            print("已初始化")

    files = tracked_files()
    print(f"待上传 {len(files)} 个文件")

    entries = []
    for index, rel in enumerate(files, 1):
        raw = (REPO / rel).read_bytes()
        blob = call("POST", f"/repos/{repo}/git/blobs", token, {
            "content": base64.b64encode(raw).decode(),
            "encoding": "base64",
        })
        entries.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        if index % 25 == 0 or index == len(files):
            print(f"  已上传 {index}/{len(files)}")

    tree = call("POST", f"/repos/{repo}/git/trees", token, {"tree": entries})
    print("tree:", tree["sha"])

    parent = None
    try:
        ref = call("GET", f"/repos/{repo}/git/ref/heads/{branch}", token)
        parent = ref["object"]["sha"]
        print("已有提交，父提交:", parent[:8])
    except RuntimeError as exc:
        print("（远端为空，创建首个提交）", str(exc)[:80])

    commit_payload = {"message": message, "tree": tree["sha"]}
    if parent:
        commit_payload["parents"] = [parent]
    commit = call("POST", f"/repos/{repo}/git/commits", token, commit_payload)
    print("commit:", commit["sha"])

    if parent:
        call("PATCH", f"/repos/{repo}/git/refs/heads/{branch}", token,
             {"sha": commit["sha"], "force": False})
    else:
        call("POST", f"/repos/{repo}/git/refs", token,
             {"ref": f"refs/heads/{branch}", "sha": commit["sha"]})
    print(f"已推送到 {repo} 的 {branch} 分支")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
