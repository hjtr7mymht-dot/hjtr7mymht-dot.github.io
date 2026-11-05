#!/usr/bin/env python3
"""
MYTH 博客静态生成器（零依赖，纯标准库）

用法：
    python3 build.py            # 读取 posts/*.md，生成 index.html 与 posts/*.html

文章格式（posts/2026-11-05-我的文章.md）：
    ---
    title: 文章标题
    date: 2026-11-05
    tags: Python, 随笔
    summary: 一两句话的摘要，会显示在博客首页卡片上
    draft: false          # 写 true 则不发布
    ---
    正文 Markdown ...

支持的 Markdown 子集：
    # / ## / ### 标题、段落、无序/有序列表、> 引用、``` 代码块、--- 分割线
    行内：`代码` **加粗** *斜体* [链接](url) ![图片](src)
"""
import html
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POSTS_DIR = ROOT / "posts"
SITE_URL = "https://hjtr7mymht-dot.github.io"
BLOG_URL = SITE_URL + "/blog/"
CST = timezone(timedelta(hours=8))


# ---------------------------------------------------------------- front matter
def parse_front_matter(text):
    m = re.match(r"\s*---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    return meta, m.group(2)


def load_posts():
    posts = []
    for f in sorted(POSTS_DIR.glob("*.md")):
        meta, body = parse_front_matter(f.read_text(encoding="utf-8"))
        if not meta.get("title") or not meta.get("date"):
            print(f"  ! 跳过 {f.name}：缺少 title/date")
            continue
        if meta.get("draft", "").lower() in ("true", "yes", "1"):
            print(f"  - 跳过 {f.name}（草稿）")
            continue
        date = meta["date"]
        slug = meta.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", f.stem)
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            print(f"  ! 跳过 {f.name}：date 需要 YYYY-MM-DD 格式")
            continue
        posts.append({
            "title": meta["title"],
            "date": date,
            "date_obj": parsed_date,
            "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            "summary": meta.get("summary", ""),
            "slug": slug,
            "url": f"posts/{slug}.html",
            "body": body,
            "source": f.name,
        })
    posts.sort(key=lambda p: p["date_obj"], reverse=True)
    return posts


# ---------------------------------------------------------------- markdown
INLINE_PATTERNS = [
    (re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)"),
     lambda m: f'<img src="{m.group(2)}" alt="{html.escape(m.group(1))}">'),
    (re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)"),
     lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>'),
    (re.compile(r"\*\*([^*]+)\*\*"), lambda m: f"<strong>{m.group(1)}</strong>"),
    (re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)"), lambda m: f"<em>{m.group(1)}</em>"),
    (re.compile(r"`([^`]+)`"), lambda m: f"<code>{m.group(1)}</code>"),
]


def render_inline(text):
    text = html.escape(text, quote=False)
    # 转义会把反引号/星号/方括号保留原样，正好继续做行内替换
    for pat, repl in INLINE_PATTERNS:
        text = pat.sub(repl, text)
    return text


def render_list(lines, ordered):
    tag = "ol" if ordered else "ul"
    items = []
    for ln in lines:
        content = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", ln)
        items.append(f"<li>{render_inline(content)}</li>")
    return f"<{tag}>" + "".join(items) + f"</{tag}>"


def render_markdown(src):
    lines = src.replace("\r\n", "\n").split("\n")
    out, i = [], 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # 代码块
        m = re.match(r"\s*```(\w*)", line)
        if m:
            lang = m.group(1)
            i += 1
            buf = []
            while i < n and not re.match(r"\s*```", lines[i]):
                buf.append(lines[i])
                i += 1
            i += 1
            code = html.escape("\n".join(buf))
            cls = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>{code}</code></pre>")
            continue

        # 标题
        m = re.match(r"(#{1,4})\s+(.*)", line)
        if m:
            raw = len(m.group(1))
            lvl = 2 if raw <= 2 else raw   # 文章标题已是 h1，# 和 ## 都渲染成 h2
            lvl = min(lvl, 4)
            text = m.group(2).strip()
            anchor = re.sub(r"[^\w\u4e00-\u9fa5-]", "", text.replace(" ", "-").lower())
            out.append(f'<h{lvl} id="{anchor}">{render_inline(text)}</h{lvl}>')
            i += 1
            continue

        # 分割线
        if re.match(r"\s*---+\s*$", line):
            out.append("<hr>")
            i += 1
            continue

        # 引用
        if re.match(r"\s*>\s?", line):
            buf = []
            while i < n and re.match(r"\s*>\s?", lines[i]):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            inner = render_markdown("\n".join(buf))
            out.append(f"<blockquote>{inner}</blockquote>")
            continue

        # 列表
        if re.match(r"\s*[-*]\s+", line) or re.match(r"\s*\d+\.\s+", line):
            ordered = bool(re.match(r"\s*\d+\.\s+", line))
            buf = []
            while i < n and (re.match(r"\s*[-*]\s+", lines[i]) or re.match(r"\s*\d+\.\s+", lines[i])):
                buf.append(lines[i])
                i += 1
            out.append(render_list(buf, ordered))
            continue

        # 空行
        if not line.strip():
            i += 1
            continue

        # 段落（连续非空行）
        buf = []
        while i < n and lines[i].strip() and not re.match(
            r"\s*(```|#{1,4}\s|[-*]\s|\d+\.\s|>)", lines[i]
        ):
            buf.append(lines[i])
            i += 1
        out.append(f"<p>{render_inline(' '.join(l.strip() for l in buf))}</p>")

    return "\n".join(out)


# ---------------------------------------------------------------- templates
def page_head(title, description, depth, page_url):
    # depth: 页面相对 blog/ 根的层级（index=0，posts/xxx=1）
    blog_up = "../" * depth     # 相对 blog 根
    site_up = blog_up + "../"   # 相对站点根（index.html 所在）
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <meta name="description" content="{html.escape(description)}">
    <meta property="og:title" content="{html.escape(title)}">
    <meta property="og:description" content="{html.escape(description)}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{page_url}">
    <link rel="alternate" type="application/rss+xml" title="MYTH 的博客" href="{blog_up}feed.xml">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <script>
        (function () {{
            var t = localStorage.getItem('theme');
            if (!t) t = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', t);
            // 入场动画只在 JS 可用时生效；blog.js 没跑起来就 3.5 秒后自动取消隐藏
            document.documentElement.classList.add('js-anim');
            setTimeout(function () {{
                if (!window.__blogReady) document.documentElement.classList.remove('js-anim');
            }}, 3500);
        }})();
    </script>
    <link rel="stylesheet" href="{blog_up}assets/blog.css">
</head>
<body>
<nav id="navbar">
    <div class="nav-inner">
        <a href="{site_up}index.html" class="nav-logo">
            <span class="logo-icon">M</span>
            MYTH
        </a>
        <ul class="nav-links" id="navLinks">
            <li><a href="{site_up}index.html">首页</a></li>
            <li><a href="{site_up}index.html#about">关于</a></li>
            <li><a href="{site_up}index.html#repos">GitHub</a></li>
            <li><a href="{site_up}index.html#wechat">公众号</a></li>
            <li><a href="{blog_up}index.html" class="{'active' if depth == 0 else ''}">博客</a></li>
            <li><a href="{site_up}index.html#contact">联系</a></li>
        </ul>
        <button class="nav-toggle" id="navToggle" aria-label="菜单">
            <span></span><span></span><span></span>
        </button>
        <button class="nav-theme-toggle" id="themeToggle" aria-label="切换主题">
            <svg class="moon-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
            <svg class="sun-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="19.78" y1="4.22" x2="18.36" y2="5.64"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/></svg>
        </button>
    </div>
</nav>
"""


def page_foot(depth):
    blog_up = "../" * depth
    site_up = blog_up + "../"
    return f"""<footer class="site-footer">
    <div class="footer-inner">
        <p>© 2026 MYTH · 用 Python 生成的静态博客</p>
        <div class="footer-links">
            <a href="{site_up}index.html">首页</a>
            <a href="{site_up}index.html#repos">开源项目</a>
            <a href="https://github.com/hjtr7mymht-dot" target="_blank" rel="noopener">GitHub</a>
            <a href="{blog_up}feed.xml">RSS</a>
        </div>
    </div>
</footer>
<script src="{blog_up}assets/blog.js"></script>
</body>
</html>
"""


def build_index(posts):
    cards = []
    for p in posts:
        tags = "".join(f'<span class="tag">{t}</span>' for t in p["tags"])
        y, m, d = p["date"].split("-") if len(p["date"].split("-")) == 3 else ("", "", "")
        card = f"""        <article class="post-card fade-up">
            <div class="post-card-meta">
                <time datetime="{p['date']}">{y} 年 {int(m)} 月 {int(d)} 日</time>
                {tags}
            </div>
            <h2 class="post-card-title"><a href="{p['url']}">{html.escape(p['title'])}</a></h2>
            <p class="post-card-summary">{html.escape(p['summary'])}</p>
            <a class="post-card-more" href="{p['url']}">阅读全文 <span>→</span></a>
        </article>"""
        cards.append(card)

    body = f"""<main class="container blog-main">
    <header class="blog-header fade-up">
        <div class="section-label">Blog</div>
        <h1 class="section-title">MYTH 的博客</h1>
        <p class="section-desc">写点儿做东西过程中的真实记录：AI 工具拆解、Python 自动化、物联网实践。不追热点，只写自己动手验证过的。</p>
    </header>
    <div class="post-list">
{chr(10).join(cards)}
    </div>
    <p class="feed-hint fade-up">订阅更新：<a href="feed.xml">RSS Feed</a></p>
</main>
"""
    head = page_head(
        "MYTH 的博客 | AI 产品 × Python 自动化",
        "MYTH 的个人博客：AI 工具拆解、Python 自动化与物联网实践的真实记录。",
        0,
        BLOG_URL,
    )
    (ROOT / "index.html").write_text(head + body + page_foot(0), encoding="utf-8")
    print(f"  ✓ index.html（{len(posts)} 篇文章）")


def build_post(p, prev_post, next_post):
    content = render_markdown(p["body"])
    tags = "".join(f'<span class="tag">{t}</span>' for t in p["tags"])
    y, m, d = p["date"].split("-")

    nav_html = ""
    if next_post:  # 列表更靠前 = 更新的一篇
        n_url = Path(next_post["url"]).name
        nav_html += f'<a class="post-nav-link" href="{n_url}"><span>更新一篇</span><strong>{html.escape(next_post["title"])}</strong></a>'
    if prev_post:  # 列表更靠后 = 更早的一篇
        p_url = Path(prev_post["url"]).name
        nav_html += f'<a class="post-nav-link next" href="{p_url}"><span>更早一篇</span><strong>{html.escape(prev_post["title"])}</strong></a>'

    body = f"""<main class="container post-main">
    <a class="back-link" href="../index.html">← 返回博客首页</a>
    <article class="post-article">
        <header class="post-header fade-up">
            <div class="post-card-meta">
                <time datetime="{p['date']}">{y} 年 {int(m)} 月 {int(d)} 日</time>
                {tags}
            </div>
            <h1>{html.escape(p['title'])}</h1>
            <p class="post-lede">{html.escape(p['summary'])}</p>
        </header>
        <div class="prose fade-up">
{content}
        </div>
    </article>
    {f'<div class="post-nav">{nav_html}</div>' if nav_html else ''}
</main>
"""
    head = page_head(
        f"{p['title']} | MYTH 的博客",
        p["summary"] or p["title"],
        1,
        BLOG_URL + p["url"],
    )
    out = ROOT / "posts" / f"{p['slug']}.html"
    out.write_text(head + body + page_foot(1), encoding="utf-8")
    print(f"  ✓ posts/{out.name}")


def build_feed(posts):
    items = []
    for p in posts[:20]:
        link = BLOG_URL + p["url"]
        desc = html.escape(p["summary"] or p["title"])
        items.append(f"""    <item>
      <title>{html.escape(p['title'])}</title>
      <link>{link}</link>
      <guid>{link}</guid>
      <pubDate>{p['date_obj'].replace(tzinfo=CST).strftime('%a, %d %b %Y %H:%M:%S +0800')}</pubDate>
      <description>{desc}</description>
    </item>""")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>MYTH 的博客</title>
    <link>{BLOG_URL}</link>
    <description>AI 工具拆解、Python 自动化与物联网实践的真实记录。</description>
    <language>zh-cn</language>
{chr(10).join(items)}
  </channel>
</rss>
"""
    (ROOT / "feed.xml").write_text(xml, encoding="utf-8")
    print("  ✓ feed.xml")


def main():
    print("构建博客…")
    posts = load_posts()
    if not posts:
        print("  没有找到文章，posts/ 目录是空的？")
        sys.exit(1)
    build_index(posts)
    for idx, p in enumerate(posts):
        newer = posts[idx - 1] if idx > 0 else None   # 列表倒序，idx-1 是更新的一篇
        older = posts[idx + 1] if idx < len(posts) - 1 else None
        build_post(p, prev_post=older, next_post=newer)
    build_feed(posts)
    print(f"完成：{len(posts)} 篇文章")


if __name__ == "__main__":
    main()
