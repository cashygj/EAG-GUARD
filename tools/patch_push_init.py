from pathlib import Path

p = Path(r"D:\EAG-GUARD\tools\push_via_api.py")
t = p.read_text(encoding="utf-8")

anchor = "    files = tracked_files()"
init = '''    # 空仓库不允许直接建 blob（409），先用 Contents API 放一个 README 初始化
    try:
        call("POST", f"/repos/{repo}/git/blobs", token, {"content": "e30=", "encoding": "base64"})
    except RuntimeError as exc:
        if "409" in str(exc):
            print("仓库为空，先初始化 README ...")
            call("PUT", f"/repos/{repo}/contents/README.md", token, {
                "message": "初始化仓库",
                "content": base64.b64encode("# EAG-Guard\\n\\n初始化占位，随后由脚本覆写。\\n".encode()).decode(),
            })
            print("已初始化")

'''
if anchor in t and "仓库为空" not in t:
    t = t.replace(anchor, init + anchor, 1)
    p.write_text(t, encoding="utf-8")
    print("已加入空仓库初始化逻辑")
else:
    print("未修改（已存在或锚点缺失）")
