# MYTH 的个人博客

纯静态博客，由 `build.py` 从 `posts/*.md` 生成，零第三方依赖（只用 Python 标准库）。

## 发一篇新文章

1. 新建 `posts/2026-12-01-文章标题.md`（文件名日期前缀会自动生成 slug）：

    ---
    title: 文章标题
    date: 2026-12-01
    slug: my-post-slug
    tags: Python, 随笔
    summary: 一两句话的摘要，显示在博客首页卡片上
    draft: false
    ---

    正文 Markdown……二级标题用 `##`，代码块用三个反引号包起来，
    支持 **加粗**、`行内代码`、[链接](https://example.com)、> 引用、列表。

    注意：`slug` 建议用英文/拼音，生成的网址更好分享；不写就用文件名去掉日期。

2. 生成并发布：

```bash
cd blog
python3 build.py
cd ..
git add -A && git commit -m "博客更新：文章标题" && git push
```

GitHub Pages 约 1 分钟内自动上线：https://hjtr7mymht-dot.github.io/blog/

## 支持的 Markdown 语法

标题（`#` 和 `##` 渲染成 h2，`###` → h3，`####` → h4）、段落、无序/有序列表、
`>` 引用、三反引号代码块（按语言加类名）、`---` 分割线、行内 `代码`、`**加粗**`、
`*斜体*`、`[链接]()`、`![图片]()`。

**不支持表格**（站点里避免用表格）。

## 目录结构

```
blog/
├── build.py        # 生成器（模板、Markdown 渲染都在这里）
├── posts/          # 文章源文件 .md —— 唯一需要手写的地方
│   └── *.html      # 生成产物，需要一起提交
├── assets/
│   ├── blog.css    # 样式，设计变量与主页一致
│   └── blog.js     # 主题切换 / 移动菜单 / 入场动画
├── index.html      # 生成产物：博客首页
└── feed.xml        # 生成产物：RSS
```

## 注意

- 主题状态与主页共用 `localStorage` 的 `theme` 键，两边切换互相同步
- `posts/*.html` 和 `index.html` 是生成产物但**必须提交**（GitHub Pages 只发静态文件）
- 改了 `build.py` 的模板或改了 `.md` 之后，要重新 `python3 build.py` 才生效
- `draft: true` 的文章不会被生成发布
