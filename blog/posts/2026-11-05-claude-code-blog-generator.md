---
title: 用 Claude Code 搭个人博客生成器，踩坑比想象中少
date: 2026-11-05
slug: claude-code-blog-generator
tags: AI工具评测, 真实记录
summary: 纯标准库撸了个零依赖静态博客生成器
draft: false
---

博客开了快一个月，一直想有个「丢一个 Markdown 进去就出网页」的东西，又不想引入 Hugo / Hexo 那套重依赖。最近用 Claude Code 把这个生成器撸出来了，零依赖、纯 Python 标准库，记一下真实体感。

一开始也考虑过 Hugo，但 Windows 上装环境、配主题、改模板那一套太重——我这隐星 P15 主要跑 RTX4060 干别的，不想为个博客折腾 Go 工具链。我的需求其实很小：一个 `.md` 进去，自动出文章页、首页列表和 RSS。需求小，自己写反而最快。

跟 Claude Code 说清楚三件事就成了：读 `blog/posts/*.md`，每篇从 front-matter 取 `title / date / slug / tags / summary / draft`；复用我站点现成的 CSS 变量和同一个 `localStorage` 主题键，保证暗色模式和主页完全一致；输出 `index.html`、`feed.xml` 和 `posts/*.html`。它给了一版 `build.py`，我边跑边改：`##` 被渲染成了三级标题、首屏淡入动画在后台标签页不触发、导航栏那条 `fixed` 规则把文章底部的「更早一篇」翻页浮空了……都是小坑，但它定位挺准，基本我说现象它就给补丁。

最大的体感是：AI 写骨架很快，但「和现有站点风格统一」这种隐性约束，得我一句句喂。比如我强调「绝不能用 Markdown 表格，用逗号分隔对比」，它第一次还是忍不住画表，被我打回去重来。还有图片，我让它别加 `loading=lazy`，因为静态站图片就那么几张，懒加载反而让首屏空一块。

顺手还把 RSS 接进了主页：首页现在用 `fetch` 读 `blog/feed.xml`，自动把最新文章拉成卡片，GitHub 的 star / repo 数也改成接口实时取。写文章这件事，从「想发→改三个文件→手摆首页」变成了「新建一个 `YYYY-MM-DD-slug.md`，填六行 front-matter，跑一下 `python3 build.py`，提交，推送」，完事。整个过程没装任何第三方包。

对只想安安静静写点东西的人来说，这种「小到能全看懂」的生成器，比重型框架省心太多。代码量不大，但每一行我都认识，哪天想加个标签云或者归档页，自己改就行。

下一篇打算写 Cursor 和 Trae 在国内网络下的体感对比——这俩我天天换着用，有些槽点不吐不快。
