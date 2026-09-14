#!/usr/bin/env python3
"""Blog build script for the homepage repo.

Usage:  python3 build.py

- Reads Markdown posts from _posts/*.md (front matter: title, date, tags, summary)
- Generates the blog:  blog/index.html (list) + blog/<slug>.html (posts)
- Injects the latest posts into index.html between the BLOG:RECENT markers
- blog/admin.html (the online editor) is hand-maintained; edit it directly
- On first run it bootstraps a local .venv with the required packages,
  so `python3 build.py` is the only command you ever need.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(ROOT, "_posts")
SITE = "https://shiyiXiao05.github.io/homepage"

# giscus 评论配置：到 giscus.app 生成后把两个 ID 填进来即可开启评论区（留空则不渲染）
GISCUS_REPO = "ShiyiXiao05/homepage"
GISCUS_REPO_ID = "R_kgDOStnO4Q"
GISCUS_CATEGORY = "Announcements"
GISCUS_CATEGORY_ID = "DIC_kwDOStnO4c4DFbGe"

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
from pygments.formatters import HtmlFormatter  # noqa: E402

PYG_LIGHT = HtmlFormatter(style="friendly").get_style_defs(".codehilite")
PYG_DARK = HtmlFormatter(style="monokai").get_style_defs('[data-theme="dark"] .codehilite')

# ---------------------------------------------------------------- markdown

def md_to_html(text):
    """Return (html, toc_html)."""
    md = markdown.Markdown(
        extensions=["pymdownx.arithmatex", "fenced_code", "tables", "codehilite", "toc"],
        extension_configs={
            "pymdownx.arithmatex": {"generic": True},
            "codehilite": {"noclasses": False, "pygments_style": "friendly", "guess_lang": False},
            "toc": {"toc_depth": "2-3"},
        },
    )
    html = md.convert(text)
    html = re.sub(r"<blockquote>\s*<p><strong>随想</strong></p>",
                  '<blockquote class="author-note"><p class="author-note-title">随想</p>', html)
    return html, md.toc

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

def xml_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

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
    body, toc = md_to_html(body)
    body = add_figures(body)
    return {
        "fname": fname,
        "slug": re.sub(r"^\d{4}-\d{2}-\d{2}-", "", fname[:-3]),
        "date": date,
        "date_disp": date.replace("-", "."),
        "title": meta.get("title", fname),
        "summary": meta.get("summary", ""),
        "tags": tags,
        "minutes": reading_minutes(body),
        "body": body,
        "toc": toc,
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
var metaTheme=document.getElementById('metaTheme');
var UI={zh:{home:'主页',blog:'博客',back:'返回列表',newer:'较新一篇',older:'较旧一篇',toc:'目录',langA:'切换语言',themeA:'切换配色主题',clear:'清除筛选',likeA:'点赞这篇文章'},en:{home:'Home',blog:'Blog',back:'All posts',newer:'Newer',older:'Older',toc:'Contents',langA:'Switch language',themeA:'Toggle color theme',clear:'Clear filter',likeA:'Like this post'}};
var cur=(function(){try{return localStorage.getItem('sx-lang')==='en'?'en':'zh'}catch(e){return 'zh'}})();
function applyTheme(t){document.documentElement.dataset.theme=t;
  if(metaTheme)metaTheme.content=t==='dark'?'#191b21':'#faf8f2';}
function fmtRT(){document.querySelectorAll('.rt').forEach(function(el){
  el.textContent=(cur==='zh'?'约 ':'')+el.dataset.min+(cur==='zh'?' 分钟':' min');});}
function setLang(l){cur=l;document.documentElement.lang=l==='zh'?'zh-CN':'en';
  var els=document.querySelectorAll('[data-ui]');
  for(var i=0;i<els.length;i++){var v=UI[l][els[i].dataset.ui];if(v)els[i].textContent=v;}
  langBtn.textContent=l==='zh'?'EN':'中';
  langBtn.setAttribute('aria-label',UI[l].langA);
  themeBtn.setAttribute('aria-label',UI[l].themeA);
  fmtRT();
  var lb=document.getElementById('likeBtn');
  if(lb){var la=UI[l].likeA;if(la)lb.setAttribute('aria-label',la);}
  try{localStorage.setItem('sx-lang',l);}catch(e){}}
langBtn.addEventListener('click',function(){setLang(cur==='zh'?'en':'zh')});
themeBtn.addEventListener('click',function(){
  applyTheme(document.documentElement.dataset.theme==='dark'?'light':'dark');
  try{localStorage.setItem('sx-theme',document.documentElement.dataset.theme);}catch(e){}
  if(window.giscusSync)window.giscusSync();});
var likeBtn=document.getElementById('likeBtn');
if(likeBtn){(function(){
  var slug=likeBtn.dataset.slug;
  var likedKey='sx-liked-'+slug;
  var liked=(function(){try{return localStorage.getItem(likedKey)==='1'}catch(e){return false}})();
  var cEl=document.getElementById('likeCount');
  function setCount(n){if(typeof n==='number')cEl.textContent=n;}
  function render(){likeBtn.classList.toggle('liked',liked);likeBtn.setAttribute('aria-pressed',liked?'true':'false');}
  fetch('https://abacus.jasoncameron.dev/get/shiyi-blog/'+slug).then(function(r){return r.json()}).then(function(d){setCount(d.value||0)}).catch(function(){});
  if(liked)render();
  likeBtn.addEventListener('click',function(){
    if(liked)return;
    fetch('https://abacus.jasoncameron.dev/hit/shiyi-blog/'+slug).then(function(r){return r.json()}).then(function(d){setCount(d.value||0)}).catch(function(){});
    liked=true;try{localStorage.setItem(likedKey,'1')}catch(e){}
    render();likeBtn.classList.add('pop');setTimeout(function(){likeBtn.classList.remove('pop')},600);
  });
})();} 
applyTheme(document.documentElement.dataset.theme||'light');
window.giscusSync=function(){var f=document.querySelector('iframe.giscus-frame');if(f)
  f.contentWindow.postMessage({giscus:{setConfig:{theme:document.documentElement.dataset.theme==='dark'?'dark':'light'}}},'https://giscus.app');};
if(document.querySelector('.tagrow')){(function(){
  var active='';
  function apply(){document.querySelectorAll('.plist li').forEach(function(li){
    var ts=(li.dataset.tags||'').split('|');
    var show=!active||ts.indexOf(active)>=0;
    li.style.display=show?'':'none';});
    document.querySelectorAll('.tagchip').forEach(function(c){
      c.classList.toggle('on',c.dataset.tag===active&&active!=='');});
    var clr=document.getElementById('clearChip');if(clr)clr.hidden=!active;}
  document.querySelector('.tagrow').addEventListener('click',function(e){
    var c=e.target.closest('.tagchip');if(!c)return;
    active=(active===c.dataset.tag)?'':c.dataset.tag;apply();});
  var q=new URLSearchParams(location.search).get('tag');
  if(q){active=q;}
  apply();
})();} 
setLang(cur);
"""

def toggles_html():
    return ('<div class="toggles">'
            '<button id="langBtn" class="tgl" type="button" aria-label="Switch language">EN</button>'
            '<button id="themeBtn" class="tgl" type="button" aria-label="Toggle theme">◐</button>'
            '</div>')

# ---------------------------------------------------------------- CSS

CSS = """
:root{--bg:#faf8f2;--ink:#201f1c;--body:#45433c;--muted:#7c786c;--border:#e6e1d5;--blue:#195fae;--hover:#c7401f;--like:#c7401f;--card:#f4f1e8;--sel:rgba(25,95,174,.13);color-scheme:light;
--sans:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei','Noto Sans SC',sans-serif;
--mono:'SF Mono','Cascadia Code','JetBrains Mono',Menlo,Consolas,monospace;
--serif:Charter,'Bitstream Charter','Sitka Text',Cambria,'Songti SC','Noto Serif CJK SC',serif;}
[data-theme="dark"]{--bg:#191b21;--ink:#e7e7e3;--body:#c4c4c0;--muted:#96948e;--border:#2f313a;--blue:#8fb0de;--hover:#e08856;--card:#22242b;--sel:rgba(143,176,222,.2);color-scheme:dark;}
@media(prefers-color-scheme:dark){:root:not([data-theme]){--bg:#191b21;--ink:#e7e7e3;--body:#c4c4c0;--muted:#96948e;--border:#2f313a;--blue:#8fb0de;--hover:#e08856;--like:#e08856;--card:#22242b;--sel:rgba(143,176,222,.2);color-scheme:dark;}}
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
.plist li:last-child{border-bottom:none}
.plist a{display:flex;align-items:baseline;gap:16px;padding:13px 6px;transition:background-color .15s ease,padding-left .15s ease}
.plist a:hover{background:var(--card);text-decoration:none;padding-left:12px}
.plist .nd{font-family:var(--mono);font-size:13px;color:var(--muted);flex:none;transition:color .15s}
.plist a:hover .nd{color:var(--blue)}
.plist .pt{flex:1;color:var(--ink);font-size:15.5px}
.plist .arrow{color:var(--blue);opacity:0;transition:opacity .15s;font-family:var(--mono)}
.plist a:hover .arrow{opacity:1}
.plist .p-sum{font-size:13px;color:var(--muted);line-height:1.55;margin-top:2px}
article h1{font-family:var(--serif);font-size:30px;font-weight:700;color:var(--ink);line-height:1.4;margin:10px 0 10px}
.post-meta{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;margin:0 0 14px;padding-bottom:14px;border-bottom:1px solid var(--border)}
.post-date,.rt{font-family:var(--mono);font-size:13px;color:var(--muted)}
.chip{display:inline-block;border:1px solid var(--border);border-radius:14px;padding:1px 11px;font-size:12px;color:var(--blue)}
article .body{font-size:15.5px;line-height:1.85}
.body h2{font-family:var(--serif);font-size:21px;font-weight:600;color:var(--ink);margin:34px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--border);scroll-margin-top:24px}
.body h3{font-size:17px;font-weight:600;color:var(--ink);margin:24px 0 10px;scroll-margin-top:24px}
.toc{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px 16px;margin:0 0 22px}
.toc summary{font-family:var(--mono);font-size:13px;color:var(--muted);cursor:pointer}
.toc summary:hover{color:var(--blue)}
.toc ul{margin:8px 0 4px;padding-left:20px}
.toc li{margin:3px 0;list-style:none}
.toc a{color:var(--body)} .toc a:hover{color:var(--blue)}
.tagrow{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px}
.tagchip{display:inline-block;border:1px solid var(--border);border-radius:14px;padding:1px 12px;font-size:12.5px;color:var(--muted);cursor:pointer;background:var(--bg)}
.tagchip:hover{color:var(--blue);border-color:var(--blue)}
.tagchip.on{background:var(--blue);border-color:var(--blue);color:#fff}
.tagchip[hidden]{display:none}
.body p{margin:13px 0}
.body ul,.body ol{margin:13px 0;padding-left:24px}
.body li{margin:6px 0}
.body img{max-width:100%;height:auto}
[data-theme="dark"] .body img[src$=".svg"]{filter:invert(1) hue-rotate(180deg)}
figure{margin:20px 0;text-align:center}
figure img{border:1px solid var(--border);border-radius:8px}
figcaption{font-family:var(--mono);font-size:12px;color:var(--muted);margin-top:9px;line-height:1.5}
.body blockquote{border-left:3px solid var(--border);padding:2px 0 2px 16px;color:var(--muted);margin:15px 0}
.body blockquote p{margin:6px 0}
.body blockquote.author-note{border:1px solid var(--border);border-left:3px solid var(--blue);border-radius:0 10px 10px 0;background:var(--card);color:var(--body);padding:16px 20px;margin:24px 0;line-height:1.9}
.body .author-note .author-note-title{color:var(--blue);font-family:var(--sans);font-size:12px;font-weight:600;letter-spacing:.14em;margin:0 0 10px}
.body .author-note p{margin:10px 0}
.body .author-note>:last-child{margin-bottom:0}
@media(max-width:520px){.body blockquote.author-note{padding:14px 16px}}

.body code{font-family:var(--mono);font-size:.86em;background:var(--card);border:1px solid var(--border);border-radius:4px;padding:1px 5px}
.codehilite{border:1px solid var(--border);border-radius:8px;overflow-x:auto;margin:16px 0}
.codehilite pre{margin:0;padding:13px 15px;font-family:var(--mono);font-size:13px;line-height:1.65}
.codehilite code{background:none;border:none;padding:0;font-size:inherit}
.comments{margin-top:36px;border-top:1px solid var(--border);padding-top:20px}
.comments h2{font-size:16px;margin-bottom:14px}
.katex-display{overflow-x:auto;overflow-y:hidden;padding:4px 0}
.end-mark{text-align:center;color:var(--muted);font-family:var(--mono);letter-spacing:.6em;margin:36px 0 0}
.likebox{text-align:center;margin:22px 0 0}
.likebtn{display:inline-flex;align-items:center;gap:9px;border:1px solid var(--border);border-radius:999px;padding:9px 22px;background:var(--surface);color:var(--muted);cursor:pointer;font-family:var(--mono);font-size:14px;transition:color .15s,border-color .15s}
.likebtn:hover{color:var(--like);border-color:var(--like)}
.likebtn svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.8;transition:fill .2s,stroke .2s}
.likebtn.liked{color:var(--like);border-color:var(--like)}
.likebtn.liked svg{fill:var(--like);stroke:var(--like)}
.likebtn.pop svg{animation:likepop .55s ease}
@keyframes likepop{0%{transform:scale(1)}45%{transform:scale(1.3)}70%{transform:scale(.92)}100%{transform:scale(1)}}
.likebtn .likecount{font-family:var(--mono);font-size:13.5px}
.post-nav{display:flex;justify-content:space-between;gap:16px;margin-top:26px;padding-top:16px;border-top:1px solid var(--border)}
.post-nav a{font-family:var(--mono);font-size:13px;max-width:48%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.post-nav a.next{text-align:right;margin-left:auto}
.post-nav .lbl{color:var(--muted);margin-right:6px}
.post-nav a.next .lbl{margin-right:0;margin-left:6px}
footer{margin-top:44px;padding-top:14px;border-top:1px solid var(--border);font-family:var(--mono);font-size:12.5px;color:var(--muted);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
@media(max-width:640px){.page{padding:60px 20px 56px}article h1{font-size:24px}h1.page-title{font-size:28px}.plist a{gap:12px}}
@media print{.toggles,.post-nav,.likebox{display:none!important}.page{max-width:100%;padding:0}a{color:inherit}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
"""

# ---------------------------------------------------------------- shells

FAVICON = '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 32 32\'%3E%3Crect width=\'32\' height=\'32\' rx=\'7\' fill=\'%23faf8f2\'/%3E%3Crect x=\'4\' y=\'4\' width=\'11\' height=\'11\' fill=\'%23195fae\'/%3E%3Crect x=\'17\' y=\'17\' width=\'11\' height=\'11\' fill=\'%23195fae\'/%3E%3Crect x=\'17\' y=\'4\' width=\'11\' height=\'11\' fill=\'none\' stroke=\'%23c7401f\' stroke-width=\'2\'/%3E%3Crect x=\'4\' y=\'17\' width=\'11\' height=\'11\' fill=\'none\' stroke=\'%23c7401f\' stroke-width=\'2\'/%3E%3C/svg%3E">'

PAGE_CSS = CSS + "\n/* pygments: light */\n" + PYG_LIGHT + "\n/* pygments: dark */\n" + PYG_DARK


def shell(title, body_html, katex, desc=None, path=None, og_image="/assets/og-card.png", og_type="website"):
    og = ""
    if desc:
        og += f'<meta name="description" content="{desc}">\n'
        og += f'<meta property="og:title" content="{title}">\n'
        og += f'<meta property="og:description" content="{desc}">\n'
        og += f'<meta property="og:url" content="{SITE}{path}">\n'
        og += f'<meta property="og:image" content="{SITE}{og_image}">\n'
        og += f'<meta property="og:type" content="{og_type}">\n'
        og += '<meta name="twitter:card" content="summary_large_image">\n'
    can = f'<link rel="canonical" href="{SITE}{path}">' if path else ""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="theme-color" content="#faf8f2" id="metaTheme">
{FAVICON}
{og}{can}
{THEME_HEAD}
<style>{PAGE_CSS}</style>
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
    all_tags = []
    for p in posts:
        for t in p["tags"]:
            if t not in all_tags:
                all_tags.append(t)
    tagrow = ""
    if all_tags:
        chips = "".join(f'<span class="tagchip" data-tag="{t}">{t}</span>' for t in all_tags)
        clear = f'<span class="tagchip" data-tag="" id="clearChip" hidden data-ui="clear">清除筛选</span>'
        tagrow = f'<div class="tagrow">{chips}{clear}</div>'
    rows, year = [], None
    for p in posts:
        y = p["date"][:4]
        if y != year:
            if year is not None:
                rows.append("</ul>")
            n = sum(1 for q in posts if q["date"].startswith(y))
            rows.append(f'<div class="year">{y} · {n} 篇</div><ul class="plist">')
            year = y
        sum_html = f'<span class="p-sum">{p["summary"]}</span>' if p["summary"] else ""
        tattr = "|".join(p["tags"])
        rows.append(f'<li data-tags="{tattr}"><a href="{p["slug"]}.html"><span class="nd">{p["date_disp"]}</span>'
                    f'<span class="pt">{p["title"]}{sum_html}</span><span class="arrow">→</span></a></li>')
    rows.append("</ul>")
    body = ('<a class="home-link" href="../index.html">← 主页</a>'
            '<h1 class="page-title" data-ui="blog">博客</h1>'
            + tagrow + "".join(rows))
    return shell("博客 · Shiyi Xiao", body, False)

def build_post(p, posts):
    i = posts.index(p)
    tags = "".join(f'<a class="chip" href="index.html?tag={t}">{t}</a>' for t in p["tags"])
    nav = ['<a href="index.html" data-ui="back">返回列表</a>']
    if i > 0:
        nav.insert(0, f'<a href="{posts[i-1]["slug"]}.html"><span class="lbl" data-ui="newer">较新一篇</span>← {posts[i-1]["title"]}</a>')
    if i < len(posts) - 1:
        nav.append(f'<a class="next" href="{posts[i+1]["slug"]}.html">{posts[i+1]["title"]} →<span class="lbl" data-ui="older">较旧一篇</span></a>')
    toc_html = f'<details class="toc"><summary data-ui="toc">目录</summary>{p["toc"]}</details>' if "href" in p["toc"] else ""
    giscus = ""
    if GISCUS_REPO_ID:
        giscus = (f'<div class="comments"><h2 data-ui="cmts">留言</h2>\n'
                  f'<script src="https://giscus.app/client.js"\n'
                  f'  data-repo="{GISCUS_REPO}" data-repo-id="{GISCUS_REPO_ID}"\n'
                  f'  data-category="{GISCUS_CATEGORY}" data-category-id="{GISCUS_CATEGORY_ID}"\n'
                  f'  data-mapping="pathname" data-strict="0" data-reactions-enabled="1"\n'
                  f'  data-emit-metadata="0" data-input-position="top"\n'
                  f'  data-theme="light" data-lang="zh-CN" crossorigin="anonymous" async>\n'
                  f'</script></div>')
    body = ('<a class="home-link" href="index.html">← 博客</a>'
            '<article><h1>' + p["title"] + "</h1>"
            '<div class="post-meta"><span class="post-date">' + p["date_disp"] + "</span>"
            '<span class="rt" data-min="' + str(p["minutes"]) + '"></span>' + tags + "</div>"
            + toc_html +
            '<div class="body">' + p["body"] + '</div>'
            '<div class="end-mark">∙ ∙ ∙</div>'
            + '<div class="likebox"><button id="likeBtn" class="likebtn" type="button" data-slug="' + p["slug"] + '" aria-pressed="false" aria-label="点赞这篇文章"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7.6-4.9-10.1-9.3C.3 7.9 1.9 3.9 5.7 3.9c2.2 0 3.8 1.2 6.3 3.7 2.5-2.5 4.1-3.7 6.3-3.7 3.8 0 5.4 4 3.8 7.8C19.6 16.1 12 21 12 21z"/></svg><span id="likeCount"></span></button></div>'
            '<nav class="post-nav">' + "".join(nav) + "</nav></article>"
            + giscus)
    desc = p["summary"] or p["title"]
    return shell(p["title"] + " · Shiyi Xiao", body, True, desc=desc, path="/blog/" + p["slug"] + ".html", og_type="article")

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
        f'<li><span class="nd">[{p["date_disp"][:7]}]</span><a href="blog/{p["slug"]}.html">{p["title"]}</a></li>'
        for p in posts[:3]
    )
    html = re.sub(marker_start + ".*?" + marker_end, marker_start + "\n" + items + "\n" + marker_end, html, flags=re.S)
    open(index, "w", encoding="utf-8").write(html)
    print("[build] homepage recent-posts updated")

def build_feed(posts):
    entries = ""
    for p in posts:
        url = f"{SITE}/blog/{p['slug']}.html"
        summary = xml_escape(p["summary"]) if p["summary"] else p["title"]
        entries += (f"<entry><title>{xml_escape(p['title'])}</title>"
                    f'<link href="{url}"/><id>{url}</id>'
                    f"<updated>{p['date']}T12:00:00Z</updated>"
                    f"<summary>{summary}</summary></entry>\n")
    updated = posts[0]["date"] + "T12:00:00Z" if posts else "2026-01-01T00:00:00Z"
    return (f'<?xml version="1.0" encoding="utf-8"?>\n'
            f'<feed xmlns="http://www.w3.org/2005/Atom">\n'
            f"<title>肖世屹的博客</title>\n"
            f'<link href="{SITE}/blog/"/>\n<id>{SITE}/blog/</id>\n'
            f"<updated>{updated}</updated>\n{entries}</feed>")

def build_sitemap(posts):
    urls = [f"{SITE}/", f"{SITE}/blog/"]
    lastmods = ["2026-09-12", "2026-09-12"]
    for p in posts:
        urls.append(f"{SITE}/blog/{p['slug']}.html")
        lastmods.append(p["date"])
    items = "".join(f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in zip(urls, lastmods))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + items + "\n</urlset>")

ROBOTS_TXT = ("User-agent: *\nAllow: /\n"
              f"Disallow: {SITE}/blog/admin.html\n"
              f"Sitemap: {SITE}/sitemap.xml\n")

def build_404():
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex">
<title>404 · 页面不存在</title>
<style>
:root{--bg:#F7F8FA;--ink:#1a1a1a;--muted:#767676;--border:#ddd;--blue:#1772d0;--card:#fff;
--sans:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;
--mono:'SF Mono',Menlo,Consolas,monospace;color-scheme:light}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--sans);background:var(--bg);color:var(--ink);min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:24px}
.code{font-family:var(--mono);font-size:72px;font-weight:700;letter-spacing:.1em}
.t{font-size:17px;margin:10px 0 22px}
a{color:var(--blue);text-decoration:none;margin:0 10px}
a:hover{text-decoration:underline}
.small{font-size:13px;color:var(--muted);margin-top:18px}
</style>
</head>
<body>
<div>
<div class="code">404</div>
<p class="t">这个页面不存在，或者已经被移动了。</p>
<p><a href="/homepage/">← 返回主页</a><a href="/homepage/blog/">← 返回博客</a></p>
<p class="small">Shiyi Xiao · 上海交通大学</p>
</div>
</body>
</html>"""

def inject_homepage(posts):
    index = os.path.join(ROOT, "index.html")
    html = open(index, encoding="utf-8").read()
    marker_start, marker_end = "<!-- BLOG:RECENT:START -->", "<!-- BLOG:RECENT:END -->"
    if marker_start not in html:
        print("[build] homepage markers not found — skipped recent-posts injection")
        return
    items = "".join(
        f'<li><span class="nd">[{p["date_disp"][:7]}]</span><a href="blog/{p["slug"]}.html">{p["title"]}</a></li>'
        for p in posts[:3]
    )
    html = re.sub(marker_start + ".*?" + marker_end, marker_start + "\n" + items + "\n" + marker_end, html, flags=re.S)
    open(index, "w", encoding="utf-8").write(html)
    print("[build] homepage recent-posts updated")

def main():
    files = sorted((f for f in os.listdir(POSTS_DIR) if f.endswith(".md")), reverse=True)
    posts = [parse_post(os.path.join(POSTS_DIR, f)) for f in files]

    # _posts/meta.json: optional sidecar {filename: {title, tags, summary}} managed by
    # blog/admin.html. When present it overrides front matter, so .md files stay pure prose.
    meta_path = os.path.join(POSTS_DIR, "meta.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, encoding="utf-8") as fh:
                post_meta = json.load(fh)
            for p in posts:
                m = post_meta.get(p["fname"])
                if not m:
                    continue
                p["title"] = str(m.get("title") or p["title"])
                p["summary"] = str(m.get("summary") or p["summary"])
                mt = m.get("tags")
                if isinstance(mt, list):
                    p["tags"] = [str(t).strip() for t in mt if str(t).strip()]
                elif isinstance(mt, str) and mt.strip():
                    p["tags"] = [t.strip() for t in re.findall(r"[^,\[\]\s]+", mt)]
                if m.get("date"):
                    p["date"] = str(m["date"])
                    p["date_disp"] = p["date"].replace("-", ".")
        except (ValueError, OSError) as e:
            print(f"[build] WARNING: ignoring meta.json: {e}")

    posts.sort(key=lambda p: p["date"], reverse=True)
    print(f"[build] {len(posts)} post(s) found")

    seen = {}
    for p in posts:
        if p["slug"] in seen:
            raise SystemExit(
                f"[build] ERROR: duplicate slug '{p['slug']}' — both {seen[p['slug']]} "
                f"and {p['date']}-{p['slug']}.md would overwrite the same page. Rename one file."
            )
        seen[p["slug"]] = f"{p['date']}-{p['slug']}.md"

    out = os.path.join(ROOT, "blog")
    write(os.path.join(out, "index.html"), build_index(posts))
    for p in posts:
        write(os.path.join(out, p["slug"] + ".html"), build_post(p, posts))
    # blog/admin.html (online editor) is hand-maintained; not generated here

    # 清理已删除文章留下的过期 HTML
    keep = {"index.html", "admin.html"} | {p["slug"] + ".html" for p in posts}
    for f in os.listdir(out):
        if f.endswith(".html") and f not in keep:
            os.remove(os.path.join(out, f))
            print("[build] removed stale", f)

    write(os.path.join(ROOT, "sitemap.xml"), build_sitemap(posts))
    write(os.path.join(ROOT, "robots.txt"), ROBOTS_TXT)
    write(os.path.join(ROOT, "404.html"), build_404())
    write(os.path.join(out, "feed.xml"), build_feed(posts))

    inject_homepage(posts)
    print("[build] done.")

if __name__ == "__main__":
    main()
