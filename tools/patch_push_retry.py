from pathlib import Path

p = Path(r"D:\EAG-GUARD\tools\push_via_api.py")
t = p.read_text(encoding="utf-8")

old_start = "def call(method: str, path: str, token: str, payload: dict | None = None) -> dict:"
idx = t.index(old_start)
end = t.index("def tracked_files()", idx)

new = '''def call(method: str, path: str, token: str, payload: dict | None = None) -> dict:
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


'''
t = t[:idx] + new + t[end:]
p.write_text(t, encoding="utf-8")
print("已加入重试逻辑")
