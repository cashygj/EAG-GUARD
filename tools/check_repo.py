import json
import sys
import urllib.error
import urllib.request

token = sys.argv[1]
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "dsh",
}


def get(path):
    req = urllib.request.Request("https://api.github.com" + path, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.load(r), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}"), dict(e.headers)


status, body, hdrs = get("/user")
print("鉴权:", status, "| 用户:", body.get("login"))
print("限额剩余:", hdrs.get("X-RateLimit-Remaining"), "/", hdrs.get("X-RateLimit-Limit"))

status, body, _ = get("/repos/cashygj/EAG-GUARD")
print("仓库读取:", status, "| 默认分支:", body.get("default_branch"), "| 大小:", body.get("size"), "KB")

status, body, _ = get("/repos/cashygj/EAG-GUARD/commits?per_page=3")
if status == 200:
    print("提交数:", len(body))
    for c in body:
        print("  ", c["sha"][:8], c["commit"]["message"].splitlines()[0][:50])
else:
    print("提交查询:", status, str(body)[:120])
