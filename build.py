#!/usr/bin/env python3
"""Blog build script for the homepage repo.

Usage:  python3 build.py

- Reads Markdown posts from _posts/*.md (front matter: title, date, tags, summary)
- Generates the blog:  blog/index.html (list) + blog/<slug>.html (posts)
- Injects the latest posts into index.html between the BLOG:RECENT markers
- On first run it bootstraps a local .venv with the required packages,
  so `python3 build.py` is the only command you ever need.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(ROOT, "_posts")

# ---------------------------------------------------------------- deps bootstrap

def ensure_deps():
    try:
        import markdown, pymdownx, pygments  # noqa: F401
        return
    except ImportError:
        pass
    venv_dir = os.path.join(ROOT, ".venv")
    py = os.path.join(venv_dir, "bin", "python")
    if not os.path.exists(py):
        print("[build] creating local .venv ...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
    print("[build] installing build dependencies into .venv ...")
    subprocess.check_call([py, "-m", "pip", "install", "-q", "markdown", "pymdown-extensions", "pygments"])
    os.execv(py, [py, os.path.abspath(__file__)] + sys.argv[1:])

ensure_deps()

import markdown  # noqa: E402

# ---------------------------------------------------------------- markdown

def md_to_html(text):
    md = markdown.Markdown(
        extensions=["pymdownx.arithmatex", "fenced_code", "tables", "codehilite", "toc"],
        extension_configs={
            "pymdownx.arithmatex": {"generic": True},
            "codehilite": {"noclasses": True, "pygments_style": "friendly", "guess_lang": False},
        },
    )
    return md.convert(text)

def add_figures(html):
    """Wrap standalone images in <figure> with the alt text as caption."""
    def repl(m):
        img = m.group(1)
        alt = re.search(r'alt="([^"]*)"', img)
        cap = f'<figcaption>{alt.group(1)}</figcaption>' if alt and alt.group(1) else ""
        return f"<figure>{img}{cap}</figure>"
    return re.sub(r"<p>(<img[^>]+>)</p>", repl, html)

def reading_minutes(html):
    text = re.sub(r"<[^>]+>", "", html)
    return max(1, round(len(text) / 500))

def parse_post(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    meta, body = {}, m.group(2) if m else raw
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                meta[key.strip()] = val.strip()
    fname = os.path.basename(path)
    date = meta.get("date", fname[:10])
    tags = [t.strip() for t in re.findall(r"[^,\[\]\s]+", meta.get("tags", ""))]
    body = add_figures(md_to_html(body))
    return {
        "slug": re.sub(r"^\d{4}-\d{2}-\d{2}-", "", fname[:-3]),
        "date": date,
        "date_disp": date.replace("-", "."),
        "title": meta.get("title", fname),
        "summary": meta.get("summary", ""),
        "tags": tags,
        "minutes": reading_minutes(body),
        "body": body,
    }

# ---------------------------------------------------------------- shared snippets

KATEX_INCLUDE = """
<link rel="stylesheet" href="__PFX__katex/katex.min.css">
<script defer src="__PFX__katex/katex.min.js"></script>
<script defer src="__PFX__katex/contrib/auto-render.min.js"></script>
<script>
document.addEventListener("DOMContentLoaded", function () {
  renderMathInElement(document.body, {
    delimiters: [
      {left: "$$", right: "$$", display: true},
      {left: "\\\\[", right: "\\\\]", display: true},
      {left: "\\\\(", right: "\\\\)", display: false},
      {left: "$", right: "$", display: false}
    ],
    throwOnError: false,
    macros: {
      "\\\\ket": "|#1\\\\rangle",
      "\\\\bra": "\\\\langle#1|",
      "\\\\braket": "\\\\langle #1 \\\\rangle",
      "\\\\DD": "\\\\mathrm{d}"
    }
  });
});
</script>
"""

THEME_HEAD = """
<script>
(function(){try{
  var t=localStorage.getItem('sx-theme');
  if(!t) t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
  document.documentElement.dataset.theme=t;
}catch(e){}})();
</script>
"""

THEME_JS = """
var langBtn=document.getElementById('langBtn');
var themeBtn=document.getElementById('themeBtn');
var UI={zh:{home:'主页',blog:'博客',sub:'研究笔记 · 技术教程 · 杂谈',back:'返回列表',newer:'较新一篇',older:'较旧一篇'},en:{home:'Home',blog:'Blog',sub:'Research notes · Tutorials · Misc',back:'All posts',newer:'Newer',older:'Older'}};
var cur=(function(){try{return localStorage.getItem('sx-lang')==='en'?'en':'zh'}catch(e){return 'zh'}})();
function fmtRT(){document.querySelectorAll('.rt').forEach(function(el){
  el.textContent=(cur==='zh'?'约 ':'')+el.dataset.min+(cur==='zh'?' 分钟':' min');});}
function setLang(l){cur=l;document.documentElement.lang=l==='zh'?'zh-CN':'en';
  var els=document.querySelectorAll('[data-ui]');
  for(var i=0;i<els.length;i++){var v=UI[l][els[i].dataset.ui];if(v)els[i].textContent=v;}
  langBtn.textContent=l==='zh'?'EN':'中';fmtRT();
  try{localStorage.setItem('sx-lang',l);}catch(e){}}
langBtn.addEventListener('click',function(){setLang(cur==='zh'?'en':'zh')});
themeBtn.addEventListener('click',function(){
  document.documentElement.dataset.theme=document.documentElement.dataset.theme==='dark'?'light':'dark';
  try{localStorage.setItem('sx-theme',document.documentElement.dataset.theme);}catch(e){}});
setLang(cur);
"""

def toggles_html():
    return ('<div class="toggles">'
            '<button id="langBtn" class="tgl" type="button" aria-label="Switch language">EN</button>'
            '<button id="themeBtn" class="tgl" type="button" aria-label="Toggle theme">◐</button>'
            '</div>')

# ---------------------------------------------------------------- CSS

CSS = """
:root{--bg:#fff;--ink:#1a1a1a;--body:#444;--muted:#767676;--border:#ddd;--blue:#1772d0;--hover:#f09228;--card:#f7f8fa;--sel:rgba(23,114,208,.14);color-scheme:light;
--sans:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei','Noto Sans SC',sans-serif;
--mono:'SF Mono','Cascadia Code','JetBrains Mono',Menlo,Consolas,monospace;
--serif:Charter,'Bitstream Charter','Sitka Text',Cambria,'Songti SC','Noto Serif CJK SC',serif;}
[data-theme="dark"]{--bg:#20212b;--ink:#eceef2;--body:#c6c9d2;--muted:#9a9daa;--border:#3a3c4a;--blue:#7fb0f5;--hover:#f0a85c;--card:#292b38;--sel:rgba(127,176,245,.26);color-scheme:dark;}
@media(prefers-color-scheme:dark){:root:not([data-theme]){--bg:#20212b;--ink:#eceef2;--body:#c6c9d2;--muted:#9a9daa;--border:#3a3c4a;--blue:#7fb0f5;--hover:#f0a85c;--card:#292b38;--sel:rgba(127,176,245,.26);color-scheme:dark;}}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--sans);background:var(--bg);color:var(--body);font-size:15px;line-height:1.75}
::selection{background:var(--sel)}:focus-visible{outline:2px solid var(--blue);outline-offset:2px;border-radius:2px}
a{color:var(--blue);text-decoration:none}a:hover{color:var(--hover);text-decoration:underline;text-underline-offset:3px}
.page{max-width:720px;margin:0 auto;padding:52px 28px 64px}
.toggles{position:fixed;top:14px;right:16px;display:flex;gap:8px;z-index:50}
.tgl{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:var(--mono);font-size:12px;font-weight:600;color:var(--muted);background:var(--bg);border:1px solid var(--border);cursor:pointer;transition:color .15s,border-color .15s,transform .15s}
.tgl:hover{color:var(--blue);border-color:var(--blue);transform:scale(1.08)}
.home-link{font-family:var(--mono);font-size:13px;color:var(--muted)}.home-link:hover{color:var(--blue)}
h1.page-title{font-family:var(--serif);font-size:34px;font-weight:700;color:var(--ink);margin:14px 0 6px;letter-spacing:.01em}
.page-sub{color:var(--muted);font-size:14px;font-family:var(--mono);margin-bottom:34px;padding-bottom:16px;border-bottom:1px solid var(--border)}
.year{font-family:var(--mono);font-size:13px;font-weight:600;color:var(--muted);letter-spacing:.1em;margin:26px 0 4px}
.plist{list-style:none}
.plist li{border-bottom:1px solid var(--border)}
.plist a{display:flex;align-items:baseline;gap:16px;padding:13px 6px;transition:background-color .15s ease,padding-left .15s ease}
.plist a:hover{background:var(--card);text-decoration:none;padding-left:12px}
.plist .nd{font-family:var(--mono);font-size:13px;color:var(--muted);flex:none;transition:color .15s}
.plist a:hover .nd{color:var(--blue)}
.plist .pt{flex:1;color:var(--ink);font-size:15.5px}
.plist .arrow{color:var(--blue);opacity:0;transition:opacity .15s;font-family:var(--mono)}
.plist a:hover .arrow{opacity:1}
article h1{font-family:var(--serif);font-size:30px;font-weight:700;color:var(--ink);line-height:1.4;margin:10px 0 10px}
.post-meta{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;margin:0 0 14px;padding-bottom:14px;border-bottom:1px solid var(--border)}
.post-date,.rt{font-family:var(--mono);font-size:13px;color:var(--muted)}
.chip{display:inline-block;border:1px solid var(--border);border-radius:14px;padding:1px 11px;font-size:12px;color:var(--blue)}
article .body{font-size:15.5px;line-height:1.85}
.body h2{font-family:var(--serif);font-size:21px;font-weight:600;color:var(--ink);margin:34px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--border)}
.body h3{font-size:17px;font-weight:600;color:var(--ink);margin:24px 0 10px}
.body p{margin:13px 0}
.body ul,.body ol{margin:13px 0;padding-left:24px}
.body li{margin:6px 0}
.body img{max-width:100%;height:auto}
figure{margin:20px 0;text-align:center}
figure img{border:1px solid var(--border);border-radius:8px}
figcaption{font-family:var(--mono);font-size:12px;color:var(--muted);margin-top:9px;line-height:1.5}
.body blockquote{border-left:3px solid var(--border);padding:2px 0 2px 16px;color:var(--muted);margin:15px 0}
.body blockquote p{margin:6px 0}
.body code{font-family:var(--mono);font-size:.86em;background:var(--card);border:1px solid var(--border);border-radius:4px;padding:1px 5px}
.codehilite{border:1px solid var(--border);border-radius:8px;overflow-x:auto;margin:16px 0;background:#f8f9fb}
[data-theme="dark"] .codehilite{background:#262b35}
.codehilite pre{margin:0;padding:13px 15px;font-family:var(--mono);font-size:13px;line-height:1.65}
.codehilite code{background:none;border:none;padding:0;font-size:inherit}
.katex-display{overflow-x:auto;overflow-y:hidden;padding:4px 0}
.end-mark{text-align:center;color:var(--muted);font-family:var(--mono);letter-spacing:.6em;margin:36px 0 0}
.post-nav{display:flex;justify-content:space-between;gap:16px;margin-top:26px;padding-top:16px;border-top:1px solid var(--border)}
.post-nav a{font-family:var(--mono);font-size:13px;max-width:48%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.post-nav a.next{text-align:right;margin-left:auto}
.post-nav .lbl{color:var(--muted);margin-right:6px}
.post-nav a.next .lbl{margin-right:0;margin-left:6px}
footer{margin-top:44px;padding-top:14px;border-top:1px solid var(--border);font-family:var(--mono);font-size:12.5px;color:var(--muted);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
@media(max-width:640px){.page{padding:60px 20px 56px}article h1{font-size:24px}h1.page-title{font-size:28px}.plist a{gap:12px}}
@media print{.toggles,.post-nav{display:none!important}.page{max-width:100%;padding:0}a{color:inherit}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
"""

# ---------------------------------------------------------------- shells

def shell(title, body_html, katex):
    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="theme-color" content="#ffffff" id="metaTheme">
{THEME_HEAD}
<style>{CSS}</style>
</head>
<body>
{toggles_html()}
<div class="page">
{body_html}
<footer><span>© 2026 肖世屹 · Shiyi Xiao</span><a href="../index.html" data-ui="home">主页</a></footer>
</div>
{KATEX_INCLUDE.replace("__PFX__", "") if katex else ""}
<script>{THEME_JS}</script>
</body>
</html>"""

def build_index(posts):
    rows, year = [], None
    for p in posts:
        y = p["date"][:4]
        if y != year:
            if year is not None:
                rows.append("</ul>")
            n = sum(1 for q in posts if q["date"].startswith(y))
            rows.append(f'<div class="year">{y} · {n} 篇</div><ul class="plist">')
            year = y
        rows.append(f'<li><a href="{p["slug"]}.html"><span class="nd">{p["date_disp"]}</span>'
                    f'<span class="pt">{p["title"]}</span><span class="arrow">→</span></a></li>')
    rows.append("</ul>")
    body = ('<a class="home-link" href="../index.html">← 主页</a>'
            '<h1 class="page-title" data-ui="blog">博客</h1>'
            '<p class="page-sub" data-ui="sub">研究笔记 · 技术教程 · 杂谈</p>'
            + "".join(rows))
    return shell("博客 · Shiyi Xiao", body, False)

def build_post(p, posts):
    i = posts.index(p)
    tags = "".join(f'<span class="chip">{t}</span>' for t in p["tags"])
    nav = ['<a href="index.html" data-ui="back">返回列表</a>']
    if i > 0:
        nav.insert(0, f'<a href="{posts[i-1]["slug"]}.html"><span class="lbl" data-ui="newer">较新一篇</span>← {posts[i-1]["title"]}</a>')
    if i < len(posts) - 1:
        nav.append(f'<a class="next" href="{posts[i+1]["slug"]}.html">{posts[i+1]["title"]} →<span class="lbl" data-ui="older">较旧一篇</span></a>')
    body = ('<a class="home-link" href="index.html">← 博客</a>'
            '<article><h1>' + p["title"] + "</h1>"
            '<div class="post-meta"><span class="post-date">' + p["date_disp"] + "</span>"
            '<span class="rt" data-min="' + str(p["minutes"]) + '"></span>' + tags + "</div>"
            '<div class="body">' + p["body"] + '</div>'
            '<div class="end-mark">∙ ∙ ∙</div>'
            '<nav class="post-nav">' + "".join(nav) + "</nav></article>")
    return shell(p["title"] + " · Shiyi Xiao", body, True)

# ---------------------------------------------------------------- admin editor (GitHub API)

ADMIN_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>博客后台 · Shiyi Xiao</title>
<script>
(function(){try{
  var t=localStorage.getItem('sx-theme');
  if(!t) t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
  document.documentElement.dataset.theme=t;
}catch(e){}})();
</script>
<style>
:root{--bg:#fff;--ink:#1a1a1a;--body:#444;--muted:#767676;--border:#ddd;--blue:#1772d0;--card:#f7f8fa;--ok:#1a7f37;--bad:#c0392b;color-scheme:light;
--sans:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;
--mono:'SF Mono',Menlo,Consolas,monospace}
[data-theme="dark"]{--bg:#20212b;--ink:#eceef2;--body:#c6c9d2;--muted:#9a9daa;--border:#3a3c4a;--blue:#7fb0f5;--card:#292b38;--ok:#57ab5a;--bad:#e5534b;color-scheme:dark}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--sans);background:var(--bg);color:var(--body);font-size:14px;line-height:1.7}
.page{max-width:1200px;margin:0 auto;padding:40px 24px 60px}
h1{font-size:22px;color:var(--ink);margin-bottom:4px}
.sub{color:var(--muted);font-size:13px;margin-bottom:20px}
button{font-family:var(--sans);font-size:13px;color:var(--ink);background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:6px 14px;cursor:pointer}
button:hover{border-color:var(--blue);color:var(--blue)}
button.primary{background:var(--blue);color:#fff;border-color:var(--blue)}
button.primary:hover{opacity:.88}
button.danger:hover{border-color:var(--bad);color:var(--bad)}
button:disabled{opacity:.5;cursor:not-allowed}
input,textarea{font-family:var(--sans);font-size:14px;color:var(--ink);background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:7px 10px;width:100%}
input:focus,textarea:focus{outline:2px solid var(--blue);outline-offset:1px}
textarea{font-family:var(--mono);font-size:13px;line-height:1.6;resize:vertical}
.cols{display:grid;grid-template-columns:260px 1fr 1fr;gap:18px;align-items:start}
@media(max-width:960px){.cols{grid-template-columns:1fr}}
.panel{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px}
.panel h3{font-size:13px;color:var(--muted);font-weight:600;margin-bottom:10px;text-transform:uppercase;letter-spacing:.06em}
.plist{list-style:none}.plist li{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:7px 4px;border-bottom:1px solid var(--border)}
.plist li:last-child{border-bottom:none}
.plist a{color:var(--ink);text-decoration:none;cursor:pointer;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.plist a:hover{color:var(--blue)}
.field{margin-bottom:10px}.field label{display:block;font-size:12px;color:var(--muted);margin-bottom:3px}
.status{font-size:12.5px;font-family:var(--mono);color:var(--muted);margin:10px 0}
.status.ok{color:var(--ok)}.status.bad{color:var(--bad)}
.preview{border:1px solid var(--border);border-radius:10px;padding:18px;min-height:420px;max-height:75vh;overflow-y:auto;background:var(--bg)}
.editor{min-height:420px}
.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.note{font-size:12px;color:var(--muted);margin-top:8px}
.token-row{display:flex;gap:8px}
.katex-display{overflow-x:auto;padding:4px 0}
.img-note{color:var(--muted)}
@media print{.page{display:none}}
</style>
</head>
<body>
<div class="page">
  <h1>博客后台</h1>
  <p class="sub">GitHub API 在线编辑 · ShiyiXiao05/homepage · <a href="index.html">← 返回博客</a> · <a href="../index.html">← 返回主页</a></p>

  <div class="panel" style="margin-bottom:18px">
    <h3>GitHub Token</h3>
    <div class="token-row">
      <input id="tokenInput" type="password" placeholder="粘贴 Fine-grained PAT（仅本仓库 Contents 读写）">
      <button id="saveToken" class="primary">保存</button>
      <button id="clearToken">清除</button>
    </div>
    <p class="note" id="tokenNote">Token 只保存在此浏览器的 localStorage 中，不会上传到仓库之外的任何地方。建议仅授权本仓库的 Contents: Read and write。</p>
    <p class="status" id="status"></p>
  </div>

  <div class="cols">
    <div class="panel">
      <h3>文章列表（_posts/）</h3>
      <ul class="plist" id="postList"></ul>
      <div style="margin-top:12px"><button id="newBtn">＋ 新建文章</button></div>
    </div>
    <div>
      <div class="toolbar">
        <input id="fTitle" placeholder="标题" style="flex:2;min-width:160px">
        <input id="fDate" placeholder="2026-09-11" style="flex:1;min-width:110px">
      </div>
      <div class="toolbar">
        <input id="fSlug" placeholder="文件名 slug（英文，如 my-first-post）" style="flex:2;min-width:200px">
        <input id="fTags" placeholder="标签，逗号分隔" style="flex:1;min-width:120px">
      </div>
      <div class="toolbar">
        <input id="fSummary" placeholder="摘要（列表页显示）" style="width:100%">
      </div>
      <textarea id="editor" class="editor" spellcheck="false" placeholder="在这里写 Markdown…"></textarea>
      <div class="toolbar" style="margin-top:12px">
        <button id="saveBtn" class="primary">保存并发布（commit 到 master）</button>
        <button id="deleteBtn" class="danger">删除此文</button>
      </div>
      <p class="status" id="saveStatus"></p>
    </div>
    <div>
      <div class="panel"><h3>实时预览</h3><div id="preview" class="preview"></div></div>
    </div>
  </div>
</div>

<script src="marked.min.js"></script>
<link rel="stylesheet" href="katex/katex.min.css">
<script defer src="katex/katex.min.js"></script>
<script defer src="katex/contrib/auto-render.min.js"></script>
<script>
const REPO = 'ShiyiXiao05/homepage';
const DIR  = '_posts';
const $ = id => document.getElementById(id);
let token = localStorage.getItem('sx-gh-token') || '';
let currentFile = null, currentSha = null;

function status(msg, cls){ const el=$('status'); el.textContent = msg||'\\u00a0'; el.className = 'status ' + (cls||''); }
function saveStatus(msg, cls){ const el=$('saveStatus'); el.textContent = msg||'\\u00a0'; el.className = 'status ' + (cls||''); }

function setToken(t){
  token = ($('tokenInput').value || '').trim();
  if (!token) { status('请先粘贴 Token', 'bad'); return; }
  localStorage.setItem('sx-gh-token', token);
  status('Token 已保存到本浏览器 ✓', 'ok');
  loadList();
}
$('saveToken').addEventListener('click', () => setToken());
$('clearToken').addEventListener('click', () => {
  localStorage.removeItem('sx-gh-token'); token=''; $('tokenInput').value='';
  status('Token 已清除'); $('postList').innerHTML='';
});

function b64ToUtf8(b64){
  const bin = atob(b64.replace(/\\n/g,''));
  const bytes = Uint8Array.from(bin, c => c.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}
function utf8ToB64(str){
  const bytes = new TextEncoder().encode(str);
  let bin = ''; bytes.forEach(b => bin += String.fromCharCode(b));
  return btoa(bin);
}
async function api(path, opts){
  const res = await fetch('https://api.github.com' + path, Object.assign({}, opts, {
    headers: Object.assign({
      'Authorization': 'Bearer ' + token,
      'Accept': 'application/vnd.github+json',
      'Content-Type': 'application/json'
    }, (opts && opts.headers) || {})
  }));
  if (!res.ok) throw new Error(res.status + ': ' + (await res.text()).slice(0, 300));
  return res.json();
}

async function loadList(){
  if (!token) { status('未配置 Token —— 只能浏览，无法读写。', ''); return; }
  status('加载文章列表…');
  try {
    const data = await api('/repos/' + REPO + '/contents/' + DIR);
    const ul = $('postList'); ul.innerHTML = '';
    data.filter(f => f.name.endsWith('.md')).sort().reverse().forEach(f => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.textContent = f.name; a.onclick = () => openPost(f);
      li.appendChild(a); ul.appendChild(li);
    });
    status('共 ' + ul.children.length + ' 篇文章 ✓', 'ok');
  } catch (e) { status('加载失败：' + e.message, 'bad'); }
}

async function openPost(f){
  status('读取 ' + f.name + ' …');
  try {
    const data = await api('/repos/' + REPO + '/contents/' + DIR + '/' + f.name);
    currentFile = f.name; currentSha = data.sha;
    const md = b64ToUtf8(data.content);
    $('editor').value = md;
    const fm = parseFrontMatter(md);
    $('fTitle').value = fm.title || '';
    $('fDate').value = fm.date || '';
    $('fTags').value = fm.tags || '';
    $('fSummary').value = fm.summary || '';
    $('fSlug').value = f.name.replace(/^\\d{4}-\\d{2}-\\d{2}-/, '').replace(/\\.md$/, '');
    saveStatus('已载入 ' + f.name + ' ✓', 'ok');
    preview();
  } catch (e) { saveStatus('读取失败：' + e.message, 'bad'); }
}

function parseFrontMatter(md){
  const m = md.match(/^---\\s*\\n([\\s\\S]*?)\\n---\\s*\\n?/);
  const fm = {};
  if (m) m[1].split('\\n').forEach(line => {
    const i = line.indexOf(':');
    if (i > 0) fm[line.slice(0,i).trim()] = line.slice(i+1).trim().replace(/^"|"/g, '');
  });
  if (fm.tags) fm.tags = fm.tags.replace(/[\\[\\]]/g, '');
  return fm;
}

function buildMarkdown(){
  const tags = $('fTags').value.trim();
  return '---\\n'
    + 'title: ' + $('fTitle').value.trim() + '\\n'
    + 'date: ' + $('fDate').value.trim() + '\\n'
    + 'tags: [' + tags + ']\\n'
    + 'summary: ' + $('fSummary').value.trim() + '\\n'
    + '---\\n\\n' + $('editor').value;
}

$('newBtn').addEventListener('click', () => {
  currentFile = null; currentSha = null;
  const d = new Date();
  $('fDate').value = d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
  $('editor').value = '## 小标题\\n\\n正文…';
  saveStatus('新文章模式：填好信息后点"保存并发布"', 'ok');
});

$('saveBtn').addEventListener('click', async () => {
  if (!token) { saveStatus('未配置 Token', 'bad'); return; }
  const slug = $('fSlug').value.trim(), date = $('fDate').value.trim();
  if (!slug || !/^[a-z0-9-]+$/.test(slug)) { saveStatus('slug 只能是小写英文、数字和连字符', 'bad'); return; }
  if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(date)) { saveStatus('日期格式应为 YYYY-MM-DD', 'bad'); return; }
  const fname = date + '-' + slug + '.md';
  const body = { message: 'blog: ' + (currentFile === fname ? 'update ' : 'add ') + fname, content: utf8ToB64(buildMarkdown()) };
  if (currentFile === fname && currentSha) body.sha = currentSha;
  if (currentFile && currentFile !== fname) saveStatus('注意：修改了日期或 slug，将创建新文件（旧文件请用删除按钮移除）', '');
  try {
    saveStatus('提交到 GitHub…');
    await api('/repos/' + REPO + '/contents/' + DIR + '/' + fname, {
      method: 'PUT', body: JSON.stringify(body)
    });
    currentFile = fname;
    await api('/repos/' + REPO + '/contents/' + DIR + '/' + fname).then(d => currentSha = d.sha);
    saveStatus('已发布 ' + fname + ' ✓ GitHub Pages 将在一两分钟内自动更新', 'ok');
    loadList();
  } catch (e) { saveStatus('发布失败：' + e.message, 'bad'); }
});

$('deleteBtn').addEventListener('click', async () => {
  if (!currentFile || !currentSha) { saveStatus('请先从列表打开要删除的文章', 'bad'); return; }
  if (!confirm('确定删除 ' + currentFile + ' ？此操作会直接提交到仓库。')) return;
  try {
    await api('/repos/' + REPO + '/contents/' + DIR + '/' + currentFile, {
      method: 'DELETE', body: JSON.stringify({ message: 'blog: delete ' + currentFile, sha: currentSha })
    });
    saveStatus('已删除 ' + currentFile + ' ✓', 'ok');
    currentFile = null; currentSha = null;
    $('editor').value = ''; preview();
    loadList();
  } catch (e) { saveStatus('删除失败：' + e.message, 'bad'); }
});

function preview(){
  const md = $('editor').value;
  const html = marked.parse(md);
  $('preview').innerHTML = html;
  const imgs = $('preview').querySelectorAll('img');
  imgs.forEach(i => { if (i.getAttribute('src') && !i.getAttribute('src').startsWith('http') && !i.getAttribute('src').startsWith('../'))
    i.src = i.getAttribute('src').replace(/^assets\\//, '../assets/'); });
  if (window.renderMathInElement) renderMathInElement($('preview'), {
    delimiters: [{left:'$$',right:'$$',display:true},{left:'\\\\[',right:'\\\\]',display:true},{left:'$',right:'$',display:false}],
    throwOnError: false
  });
}
$('editor').addEventListener('input', () => { preview(); });

$('tokenInput').value = token;
if (token) { status('已从本地恢复 Token ✓', 'ok'); loadList(); }
else status('未配置 Token —— 只能浏览，无法读写。');
preview();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------- build

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(content)
    print("[build] wrote", os.path.relpath(path, ROOT))

def inject_homepage(posts):
    index = os.path.join(ROOT, "index.html")
    html = open(index, encoding="utf-8").read()
    marker_start, marker_end = "<!-- BLOG:RECENT:START -->", "<!-- BLOG:RECENT:END -->"
    if marker_start not in html:
        print("[build] homepage markers not found — skipped recent-posts injection")
        return
    items = "".join(
        f'<li><span class="nd">[{p["date_disp"]}]</span><a href="blog/{p["slug"]}.html">{p["title"]}</a></li>'
        for p in posts[:3]
    )
    html = re.sub(marker_start + ".*?" + marker_end, marker_start + "\n" + items + "\n" + marker_end, html, flags=re.S)
    open(index, "w", encoding="utf-8").write(html)
    print("[build] homepage recent-posts updated")

def main():
    files = sorted((f for f in os.listdir(POSTS_DIR) if f.endswith(".md")), reverse=True)
    posts = [parse_post(os.path.join(POSTS_DIR, f)) for f in files]
    posts.sort(key=lambda p: p["date"], reverse=True)
    print(f"[build] {len(posts)} post(s) found")

    out = os.path.join(ROOT, "blog")
    write(os.path.join(out, "index.html"), build_index(posts))
    for p in posts:
        write(os.path.join(out, p["slug"] + ".html"), build_post(p, posts))
    write(os.path.join(out, "admin.html"), ADMIN_HTML)

    inject_homepage(posts)
    print("[build] done.")

if __name__ == "__main__":
    main()
