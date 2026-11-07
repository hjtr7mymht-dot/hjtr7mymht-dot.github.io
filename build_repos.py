#!/usr/bin/env python3
"""重新生成个人网站的开源项目数据 repos.json。

构建期从 GitHub API 拉取 hjtr7mymht-dot 的公开仓库，生成前端读取的同源
repos.json。优先用 GitHub token（5000 次/小时）；拿不到就匿名拉（60 次/小时，
构建期一次只拉 1 次，够用）。

前端逻辑：优先读同源 repos.json（稳定、不限速、不怕墙），失败再回退
api.github.com 实时拉取。
"""
import json, subprocess, sys, urllib.request

OWNER = "hjtr7mymht-dot"
# 网站自身仓库（不是"开源项目"，不展示）
EXCLUDE = {"hjtr7mymht-dot.github.io"}
EXCLUDE_FORKS = True
# 精选（置顶）仓库顺序
FEATURED = ["WOA_AutoBot", "REIB", "CrossClip-"]

API = "https://api.github.com"

def get_token():
    """尽力拿 token；读不到就返回 None（改匿名）。绝不在任何输出里打印 token。"""
    for cmd in [
        # 1) 环境变量
        None,
        # 2) .env 里的 GITHUB_TOKEN（只读、不打印）
        None,
    ]:
        pass
    env_tok = __import__("os").environ.get("GITHUB_TOKEN") or __import__("os").environ.get("GH_TOKEN")
    if env_tok and len(env_tok) > 10:
        return env_tok
    # .env 文件
    try:
        for line in open("/Users/drtotm/.hermes/.env"):
            line = line.strip()
            if line.startswith("#"):
                continue
            if line.startswith("GITHUB_TOKEN="):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if len(v) > 10:
                    return v
    except Exception:
        pass
    # keychain（可能卡 TCC 弹窗，短超时放弃）
    try:
        out = subprocess.run(
            ["bash", "-c", 'printf "protocol=https\\nhost=github.com\\n" | git credential fill 2>/dev/null | sed -n "s/^password=//p"'],
            capture_output=True, text=True, timeout=6,
        ).stdout.strip()
        if len(out) > 10:
            return out
    except Exception:
        pass
    return None

def get(path, token):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "myth-repos-builder"}
    if token:
        headers["Authorization"] = "token " + token
    req = urllib.request.Request(API + path, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

token = get_token()
print("token:", "有" if token else "无（匿名拉取）", file=sys.stderr)

repos = get(f"/users/{OWNER}/repos?sort=updated&type=owner&per_page=100", token)
items = []
for r in repos:
    if r["name"] in EXCLUDE:
        continue
    if EXCLUDE_FORKS and r.get("fork"):
        continue
    items.append({
        "name": r["name"],
        "html_url": r["html_url"],
        "description": r.get("description") or "",
        "language": r.get("language"),
        "stargazers_count": r.get("stargazers_count", 0),
        "forks_count": r.get("forks_count", 0),
        "updated_at": r.get("updated_at", ""),
        "featured": r["name"] in FEATURED,
    })

# 排序：featured 按 FEATURED 顺序在前，其余按 updated 倒序
feat_idx = {name: i for i, name in enumerate(FEATURED)}
def sort_key(x):
    if x["featured"]:
        return (0, feat_idx[x["name"]])
    return (1, -int(x["updated_at"][:10].replace("-", "") or "0"))

items.sort(key=sort_key)

out = {
    "generated_at": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True).stdout.strip(),
    "owner": OWNER,
    "total_repos": len(items),
    "total_stars": sum(i["stargazers_count"] for i in items),
    "repos": items,
}
with open("repos.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("repos.json 已生成：%d 个项目，总星标 %d" % (len(items), out["total_stars"]))
for i in items:
    print("  - %s%s ★%d" % ("[精选] " if i["featured"] else "", i["name"], i["stargazers_count"]))
