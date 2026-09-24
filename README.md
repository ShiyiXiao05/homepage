# 肖世屹 · 个人主页

上海交通大学人工智能学院本科生（拔尖英才试点班）的个人主页 + 博客。

- **线上地址**：<https://shiyixiao05.github.io/homepage/>
- **技术栈**：无框架。手写 HTML/CSS/JS 静态页 + 一个 Python 构建脚本（`build.py`），托管在 GitHub Pages
- **推送即发布**：push 到 `master` → GitHub Actions 跑构建 → 机器人把生成物提交回仓库 → Pages 自动重新部署

## 目录结构

```
index.html              主页（手写；只有「近期博文」区和页脚日期由构建脚本写入）
build.py                唯一的构建入口：Markdown → 博客 HTML / RSS / sitemap / robots / 404
_posts/
  YYYY-MM-DD-slug.md    文章正文（可选 front matter，见下）
  meta.json             文章元信息旁路（标题/标签/摘要/日期），由在线编辑器维护
blog/
  index.html            博客列表（生成物）
  <slug>.html           文章页（生成物）
  feed.xml              Atom 订阅（生成物）
  admin.html            浏览器内在线编辑器（手写，唯一需要 token 的页面）
  katex/                本地 KaTeX，公式离线渲染
  marked.min.js         编辑器预览用的 Markdown 解析
assets/                 头像、论文配图、OG 卡片、文章插图（assets/blog/<slug>/）
scripts/admin-token.sh  管理编辑器 PAT（存 macOS 钥匙串）
sitemap.xml robots.txt 404.html   （生成物）
.github/workflows/build.yml       push 触发构建
```

## 本地构建

```bash
python3 build.py     # 首次运行会自动创建 .venv 并安装 markdown / pymdown-extensions / pygments
```

构建是**确定性**的：内容没变时重复运行不会产生 diff。构建脚本会：

1. 渲染 `_posts/*.md` → `blog/index.html` + `blog/<slug>.html`
2. 清理已删文章遗留的旧 HTML；slug 撞车时直接报错退出
3. 生成 `blog/feed.xml`、`sitemap.xml`、`robots.txt`、`404.html`
4. 刷新 `index.html` 的「近期博文」标记区与页脚「最后更新」日期（zh/en 两份文案 + 可见文本一并写入）

> ⚠️ 除 `index.html` 的标记区外，上述 HTML/XML **都是生成物，不要手改**——下次构建会覆盖。

## 写文章

**方式 A：在线编辑器**（在外面也能发）

```bash
./scripts/admin-token.sh open    # 用钥匙串里的 PAT 打开 blog/admin.html
```

编辑器可以直接新建/编辑/删除文章与 `meta.json`、实时预览、提交到仓库，提交后 Actions 会自动重建站点。

**方式 B：本地写**——在 `_posts/` 新建 `YYYY-MM-DD-slug.md`，然后 `python3 build.py` 提交推送。

front matter 全部可选（文件名里的日期即默认日期）：

```markdown
---
title: 复赛小记（上）
date: 2026-09-12
tags: 物理, 随笔
summary: 列表页显示的一行摘要
---
```

`_posts/meta.json` 里同一文件的条目会**覆盖** front matter —— 这样 `.md` 可以保持纯正文。

正文支持：`$...$` / `$$...$$` 公式（KaTeX）、围栏代码块（Pygments 明暗双主题）、表格、`toc`（h2–h3 生成文章目录）、独立成段的图片自动包成带图注的 `<figure>`，以及以 `> **随想**` 开头的引用块（渲染成作者批注样式）。

图片放在 `assets/blog/<slug>/`，正文里用相对路径引用：`![图注](../assets/blog/<slug>/fig-1.svg)`（图注会作为图片说明显示）。

## 主页维护

- **手写区**：动态 / 教育经历 / 科研经历 / 论文 / 研究兴趣 / 所获荣誉。
- 文案在页面里出现**两次**：HTML 里一份（无 JS 时的默认值）、`<script>` 里的 `T.zh` / `T.en` 字典一份。改文案要两边同时改，否则切换语言会被字典覆盖回去。
- **自动区**：`<!-- BLOG:RECENT:START -->…<!-- BLOG:RECENT:END -->` 之间是最近 3 篇文章；页脚「最后更新 YYYY.MM」由构建时间生成。

## 配色与主题

四套和风传统色可切换（铁绀×天青 / 常盘×秘色 / 江户紫×紫苑 / 黄丹×团栗），每套都有明暗两版；另有跟随系统的深色模式、zh/EN 双语。

配色定义**分散在三处**，调色时需要一起改：

| 位置 | 作用 |
| --- | --- |
| `index.html` 的 `:root` / `[data-theme="dark"]` | 主页首屏默认色（避免闪烁） |
| `index.html` 的 `PALETTES` | 主页切换配色 |
| `build.py` 的 `CSS` / `THEME_JS` / `toggles_html()` | 博客各页的样式、配色切换、切换控件 |

## 简历 / LaTeX

简历源文件在 `output/pdf/`（XeLaTeX 编译：`xelatex 肖世屹-个人简历.tex`），中间产物在 `tmp/`。这两个目录都是本地工作区，已在 `.gitignore` 中。

## 密钥与本地私有文件

- 编辑器的 GitHub PAT 存在 **macOS 钥匙串**里（`scripts/admin-token.sh store|open|copy|show|forget`），仓库目录内**不再保留明文 token**。它需要一枚 fine-grained PAT，权限只有本仓库的 `Contents: Read and write`。
- 编辑器会把 token 存进浏览器 `localStorage`，所以换浏览器需要重新粘贴/打开一次；地址栏里的 `#t=<token>` 会被页面立刻抹掉。
- 如果 PAT 可能泄露：GitHub → Settings → Developer settings → Fine-grained tokens → 撤掉旧的，新建一枚后 `./scripts/admin-token.sh store`。
- 被忽略的本地文件：`/output/`、`/tmp/`、`/简历.tex`、`/科研计划书.doc`、`物理竞赛真题/`、`图片对比.*`、`*.local`。这些是私有材料或临时产物，**不要提交**。

## 说明

- `robots.txt` 用 `Disallow` 屏蔽 `blog/admin.html`，页面本身也带 `noindex`。
- 站点零追踪：没有统计脚本、没有广告、没有外部字体；评论走 giscus（GitHub Discussions），点赞走 Abacus（只存计数）。
- 站点规范 URL 统一为小写 `https://shiyixiao05.github.io/homepage`，`build.py` 的 `SITE` 常量、主页 `og:url` / `og:image` / `canonical`、sitemap、feed 都以此为准（GitHub 用户名的展示大小写 `ShiyiXiao05` 只出现在 github.com 链接里）。
