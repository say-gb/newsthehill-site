#!/usr/bin/env python3
"""뉴스더힐 정적 사이트 생성기.
사용: python3 build.py  → dist/ 생성 (newsthehill.com 루트용, CNAME 포함)
미리보기: BASE_PATH=/newsthehill-site/ OUT_DIR=../upload python3 build.py  (하위경로, CNAME 제외)"""
import re, html, shutil, json
from pathlib import Path
from datetime import datetime
from email.utils import format_datetime

import os
ROOT = Path(__file__).parent
DIST = Path(os.environ.get("OUT_DIR", ROOT / "dist"))
BASE = "/" + os.environ.get("BASE_PATH", "/").strip("/") + "/"
BASE = "/" if BASE == "//" else BASE  # 예: BASE_PATH=/newsthehill-site/
NO_CNAME = os.environ.get("NO_CNAME") == "1" or BASE != "/"
SITE = "https://newsthehill.com"
NAME = "뉴스더힐"
TAGLINE = "높은 시선으로 세상을, 깊은 취재로 진실을"
SECTIONS = {  # slug: 이름 (하단 탭 순서)
    "food": "식품·유통", "local": "지역", "people": "사람들",
    "opinion": "오피니언", "feature": "기획·이슈",
}
COLUMN_HEADER = "/static/column-header-sisun.jpg"

def esc(s): return html.escape(str(s), quote=True)

def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\s)(.+?)\*", r"<em>\1</em>", s)
    s = re.sub(r"\[(.+?)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', s)
    return s

def md(text):
    """작은 마크다운 변환기: ## 소제목, 문단, -/1. 목록, > 인용, **굵게**, 링크, HTML 주석 제거"""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    out, para, lst = [], [], None
    def flush():
        nonlocal para, lst
        if para: out.append("<p>" + inline(" ".join(para)) + "</p>"); para = []
        if lst: out.append(f"<{lst[0]}>" + "".join(f"<li>{inline(i)}</li>" for i in lst[1]) + f"</{lst[0]}>"); lst = None
    for line in text.splitlines():
        l = line.strip()
        if not l: flush(); continue
        m = re.match(r"(#{2,4})\s+(.*)", l)
        if m: flush(); n = min(len(m.group(1)) + 0, 4); out.append(f"<h{n}>{inline(m.group(2))}</h{n}>"); continue
        m = re.match(r"(?:[-*]|(\d+)\.)\s+(.*)", l)
        if m:
            if para: p = para; para = []; out.append("<p>" + inline(" ".join(p)) + "</p>")
            kind = "ol" if m.group(1) else "ul"
            if not lst or lst[0] != kind: flush(); lst = (kind, [])
            lst[1].append(m.group(2)); continue
        m = re.match(r"!\[(.*?)\]\((\S+?)\)$", l)
        if m: flush(); out.append(f'<figure><img src="{esc(m.group(2))}" alt="{esc(m.group(1))}" loading="lazy"></figure>'); continue
        if l.startswith(">"): flush(); out.append("<blockquote>" + inline(l.lstrip("> ")) + "</blockquote>"); continue
        if lst: flush()
        para.append(l)
    flush()
    h = "\n".join(out)
    h = re.sub(r'</figure>\n<p><em>(.*?)</em></p>', r'<figcaption>\1</figcaption></figure>', h)
    return h

def load():
    arts = []
    for f in sorted((ROOT / "articles").glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
        meta = dict(re.findall(r"^(\w+):\s*(.*)$", m.group(1), re.M)); body = m.group(2)
        if meta.get("draft", "").lower() == "true": continue
        meta.setdefault("slug", f.stem)
        meta["dt"] = datetime.strptime(meta["date"][:10], "%Y-%m-%d")
        if meta["section"] not in SECTIONS: raise SystemExit(f"{f}: 알 수 없는 section {meta['section']}")
        meta["html"] = md(body)
        plain = html.unescape(re.sub(r"<[^>]+>", "", meta["html"]))
        meta["desc"] = meta.get("subtitle") or plain[:110]
        meta["excerpt"] = plain[:90].strip() + "…"
        meta["url"] = f"/articles/{meta['slug']}/"
        meta["column"] = meta.get("column", "").lower() == "true" or (meta["section"] == "opinion" and meta.get("kind") in ("칼럼", "기고"))
        meta["kicker"] = meta.get("kind", "") if meta["section"] == "opinion" else ""
        arts.append(meta)
    arts.sort(key=lambda a: (a["dt"], a.get("time", ""), a["slug"]), reverse=True)
    return arts

WEEK = "월화수목금토일"
COLUMNISTS = [  # (이름, 연재명, 저자 문자열, 사진)
    ("최경집", "최경집 교수의 시선", "최경집", "/static/old/kj-2026101200001-0.png"),
    ("박현", "박현 손해사정사의 정당한 보험금 리포트", "박현 손해사정사", "/static/old/hyun-2026101500001-0.png"),
    ("백효연", "단지팀장의 보험칼럼", "단지팀장(백효연)", "/static/old/danji-2026100600003-0.png"),
]
EMAIL = "info@newsthehill.com"

def d(a): return a.get("display_date") or f"{a['dt']:%Y.%m.%d}"
def dt(a): return a.get("display_date") or f"{a['dt']:%Y.%m.%d}" + (f" {a['time']}" if a.get("time") else "")
def hm(a): return a.get("display_date") or f"{a['dt']:%m.%d}" + (f"<b>{a['time']}</b>" if a.get("time") else "")
def secname(a): return SECTIONS[a["section"]]
def clean(t): return re.sub(r"^\[[^\]]+\]\s*", "", t)

def today():
    n = datetime.now(); return f"{n.year}년 {n.month}월 {n.day}일({WEEK[n.weekday()]})"

LOGO = """<a class="logo" href="/" aria-label="뉴스더힐 홈"><!-- 원본 로고: 교수님 제공(2026-10-17 12:52 KST 채팅 첨부), 크롭본 static/logo/newsthehill-logo.jpg / 원본 newsthehill-logo-original.jpg --><img src="/static/logo/newsthehill-logo.jpg" alt="NEWS THE HILL 뉴스더힐" width="1058" height="237"></a>"""

def header(active, arts):
    menu = "".join(f'<a href="/section/{k}/"{" class=on" if k == active else ""}>{v}</a>' for k, v in SECTIONS.items())
    tick = "".join(f'<li><a href="{a["url"]}">{esc(a["title"])}</a></li>' for a in arts[:6])
    return f"""<header class="hd">
<div class="mast"><div class="wrap">
<p class="date"><span id="today">{today()}</span><span id="wx" class="wx"></span></p>
{LOGO}
<div class="tools"><form class="srch" action="https://www.google.com/search" role="search"><input type="hidden" name="as_sitesearch" value="newsthehill.com"><input name="q" placeholder="기사 검색" aria-label="검색어"><button aria-label="검색"><svg viewBox="0 0 20 20" width="16" height="16"><circle cx="8.5" cy="8.5" r="6" fill="none" stroke="currentColor" stroke-width="2"/><path d="M13 13l5 5" stroke="currentColor" stroke-width="2"/></svg></button></form>
<button class="ham" type="button" aria-label="전체메뉴"><svg viewBox="0 0 20 20" width="20" height="20"><path d="M2 5h16M2 10h16M2 15h16" stroke="currentColor" stroke-width="2"/></svg></button></div>
</div></div>
<nav class="gnb" aria-label="주메뉴"><div class="wrap">{menu}</div></nav>
<div class="ticker"><div class="wrap"><b>최신</b><ul id="tick">{tick}</ul></div></div>
</header>"""

FOOTER = f"""<footer class="foot">
<div class="fmenu"><div class="wrap"><a href="/about/">회사소개</a><a href="/policy/terms/">이용약관</a><a href="/policy/privacy/"><b>개인정보처리방침</b></a><a href="/policy/youth/">청소년보호정책</a><a href="mailto:{EMAIL}?subject=%EA%B8%B0%EC%82%AC%EC%A0%9C%EB%B3%B4">기사제보</a><a href="mailto:{EMAIL}?subject=%EA%B4%91%EA%B3%A0%EB%AC%B8%EC%9D%98">광고문의</a><a href="/rss.xml">RSS</a></div></div>
<div class="wrap finfo"><div class="flogo"><b>뉴스더힐</b><small>NEWS THE HILL</small></div>
<table><tbody>
<tr><th>제호</th><td>뉴스더힐</td><th>등록번호</th><td>서울, 아56252</td><th>등록일</th><td>2025.11.27</td></tr>
<tr><th>발행인·편집인</th><td>최만수</td><th>청소년보호책임자</th><td>최만수</td><th>최초 발행일</th><td>2026.03.24</td></tr>
<tr><th>도메인</th><td colspan="5">newsthehill.com</td></tr>
<tr><th>발행소</th><td colspan="5">서울 송파구 위례광장로 199, 501-30호 (장지동, 성희프라자) <span class="sep">|</span> 사무실 경기도 성남시 수정구 위례대로 83 밀리토피아호텔 B1, 21호</td></tr>
<tr><th>대표전화</th><td>02-6951-5540</td><th>팩스</th><td>070-4009-3314</td><th>이메일</th><td><a href="mailto:{EMAIL}">{EMAIL}</a></td></tr>
</tbody></table>
<p class="copy">뉴스더힐의 모든 콘텐츠(기사)는 저작권법의 보호를 받으며, 무단 전재·복사·배포 등을 금합니다. Copyright © {datetime.now().year} 뉴스더힐. All rights reserved.</p></div>
</footer>"""

SCRIPT = """<script>
(function(){var u=document.getElementById('tick');if(u&&u.children.length>1){var i=0;setInterval(function(){i=(i+1)%u.children.length;u.style.transform='translateY(-'+(i*30)+'px)'},4000)}
var W=['일','월','화','수','목','금','토'],n=new Date(),t=document.getElementById('today');if(t)t.textContent=n.getFullYear()+'년 '+(n.getMonth()+1)+'월 '+n.getDate()+'일('+W[n.getDay()]+')';
var C={0:'맑음',1:'대체로 맑음',2:'구름 조금',3:'흐림',45:'안개',48:'안개',51:'이슬비',53:'이슬비',55:'이슬비',61:'비',63:'비',65:'강한 비',71:'눈',73:'눈',75:'많은 눈',80:'소나기',81:'소나기',82:'강한 소나기',95:'뇌우'};
fetch('https://api.open-meteo.com/v1/forecast?latitude=37.48&longitude=127.14&current=temperature_2m,weather_code&timezone=Asia%2FSeoul').then(function(r){return r.json()}).then(function(j){var c=j.current;document.getElementById('wx').textContent='송파 '+(C[c.weather_code]||'')+' '+Math.round(c.temperature_2m)+'℃'}).catch(function(){});
document.querySelectorAll('.fs button').forEach(function(b){b.onclick=function(){var x=document.querySelector('.body');var s=parseFloat(getComputedStyle(x).fontSize)+(b.dataset.d==='+'?1:-1);x.style.fontSize=Math.max(14,Math.min(24,s))+'px'}});
var f=document.querySelector('.srch');if(f)f.addEventListener('submit',function(e){var i=f.querySelector('input[name=q]');if(getComputedStyle(i).display==='none'||!i.value){e.preventDefault();f.classList.add('open');i.focus()}});
var h=document.querySelector('.ham');if(h)h.onclick=function(){document.documentElement.classList.toggle('menu-open')};})();
</script><script src="/static/js/blankfill.js" data-banners="/static/banners/banners.json" defer></script>"""

def page(title, body, desc=TAGLINE, url="/", image="/static/og-default.jpg", active="", ogtype="website", arts=(), keywords=""):
    full = f"{title} - {NAME}" if title else f"{NAME} - {TAGLINE}"
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full)}</title><meta name="description" content="{esc(desc)}">{f'<meta name="keywords" content="{esc(keywords)}">' if keywords else ''}
<link rel="canonical" href="{SITE}{url}"><link rel="icon" href="/favicon.ico" sizes="32x32"><link rel="icon" type="image/png" href="/static/favicon.png"><link rel="apple-touch-icon" href="/static/favicon.png">
<meta property="og:site_name" content="{NAME}"><meta property="og:type" content="{ogtype}"><meta property="og:title" content="{esc(title or NAME)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{SITE}{url}"><meta property="og:image" content="{SITE}{image}"><meta property="og:locale" content="ko_KR">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#283043">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;700;900&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" rel="stylesheet">
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="/rss.xml"><link rel="stylesheet" href="/static/style.css">
</head><body>
{header(active, arts)}
<main class="wrap">{body}</main>
{FOOTER}
{SCRIPT}
</body></html>"""

def thumb(a, cls="th"):
    t = a.get("thumb")
    return f'<span class="{cls}"><img src="{esc(t)}" alt="" loading="lazy"></span>' if t else ""

def meta_line(a):
    return f'<em class="m">{esc(a["author"])}<i>|</i>{dt(a)}</em>'

def row(a, ex=True):  # 썸네일 + 제목 + 요약 + 기자·시각
    kicker = f'<span class="okick">{esc(a["kicker"])}</span>' if a['kicker'] else ""
    return f"""<li class="row{' nothumb' if not a.get('thumb') else ''}"><a href="{a['url']}">{thumb(a)}{kicker}<strong>{esc(a['title'])}</strong>
{f'<p>{esc(a["excerpt"])}</p>' if ex else ''}{meta_line(a)}</a></li>"""

def tline(a):
    return f'<li><a href="{a["url"]}">{esc(a["title"])}</a></li>'

def timeline(a):  # "15:05 제목"
    return f'<li><time>{hm(a)}</time><a href="{a["url"]}">{esc(a["title"])}</a></li>'

def boxh(t, href="", tag="h2"):
    more = f'<a class="more" href="{href}">더보기</a>' if href else ""
    return f'<{tag} class="bh"><span>{t}</span>{more}</{tag}>'

ADSLOT = '<div class="adslot" data-bf-slot="300x250" aria-label="광고 영역"></div>'

def rank(arts, cur=None, n=10, skip=8):
    pool = [a for a in arts[skip:] if a is not cur]
    top = [a for a in pool if not a["column"]][:n//2]; top += [a for a in pool if a["column"]][:n - len(top)]
    top.sort(key=lambda a: (a["dt"], a.get("time", "")), reverse=True)
    return f'<section class="rankbox">{boxh("주요 뉴스")}<ol class="rank">' + "".join(f'<li><b>{i+1}</b><a href="{a["url"]}">{esc(a["title"])}</a></li>' for i, a in enumerate(top)) + "</ol></section>"

def columnists(arts):
    cb = ""
    for name, series, author, ph in COLUMNISTS:
        last = next((a for a in arts if a["author"] == author), None)
        if not last: continue
        cb += f'<li><a href="{last["url"]}"><span class="cph"><img src="{ph}" alt="{esc(name)}" loading="lazy"></span><b>{esc(series)}</b><span class="ct">{esc(clean(last["title"]))}</span></a></li>'
    return f'<section class="cbox">{boxh("칼럼니스트", "/section/opinion/")}<ul>{cb}</ul></section>'

def sidebar(arts, cur=None):
    return f'<aside class="side">{rank(arts, cur)}{ADSLOT}{columnists(arts)}</aside>'

def colbox(arts):  # 「최경집 교수의 시선」 아이보리 박스
    c = next((a for a in arts if a["author"] == "최경집"), None)
    if not c: return ""
    first = re.sub(r"<[^>]+>", "", c["html"]).strip().split("\n")[0][:120]
    others = [a for a in arts if a["author"] == "최경집" and a is not c][:3]
    return f"""<section class="sisun"><a class="sface" href="{c['url']}"><img src="{COLUMNISTS[0][3]}" alt="최경집 교수"></a>
<div class="stx"><p class="slab">최경집 교수의 시선</p><a href="{c['url']}"><strong>{esc(clean(c['title']))}</strong><p>{esc(first)}…</p></a><em class="m">최경집 식품마케팅 교수<i>|</i>{dt(c)}</em></div>
<ul class="smore">{''.join(f'<li><a href="{a["url"]}">{esc(clean(a["title"]))}</a><time>{a["dt"]:%m.%d}</time></li>' for a in others)}</ul></section>"""

def write(path, s):
    p = DIST / path.lstrip("/"); p = p / "index.html" if not p.suffix else p
    if BASE != "/":  # 내부 링크·자산에 BASE 접두어 (canonical/OG는 절대주소라 영향 없음)
        s = re.sub(r'((?:href|src)=")/(?!/)', lambda m: m.group(1) + BASE, s)
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s, encoding="utf-8")

def make_thumbs(arts):
    """본문 첫 사진을 360px 썸네일로 (PIL 있으면). 칼럼은 연재 이미지, 없으면 칼럼 헤더."""
    try:
        from PIL import Image
    except ImportError:
        Image = None
    tdir = DIST / "static/thumb"; tdir.mkdir(parents=True, exist_ok=True)
    for a in arts:
        m = re.search(r'<img src="(/static/[^"]+)"', a["html"])
        src = m.group(1) if m else (COLUMN_HEADER if a["column"] else None)
        if not src: continue
        a["photo"] = src
        if Image is None: a["thumb"] = src; continue
        p = ROOT / src.lstrip("/"); out = tdir / (Path(src).stem + ".jpg")
        if not out.exists():
            im = Image.open(p).convert("RGB"); im.thumbnail((480, 480)); im.save(out, quality=80)
        a["thumb"] = "/static/thumb/" + out.name

FACES = {"kj": (0.50, 0.04, 0.96, 0.62), "hyun": (0.57, 0.10, 0.89, 0.50), "danji": (0.62, 0.06, 0.92, 0.56)}  # 연재 이미지에서 얼굴 부분(비율)
def make_faces():
    from PIL import Image
    out = {}
    for i, (name, series, author, ph) in enumerate(COLUMNISTS):
        key = Path(ph).stem.split("-")[0]; box = FACES.get(key)
        if not box: continue
        im = Image.open(ROOT / ph.lstrip("/")).convert("RGB"); w, h = im.size
        c = im.crop((int(box[0]*w), int(box[1]*h), int(box[2]*w), int(box[3]*h)))
        s = min(c.size); c = c.crop(((c.size[0]-s)//2, 0, (c.size[0]-s)//2 + s, s)).resize((160, 160))
        p = DIST / "static/thumb" / f"face-{key}.jpg"; p.parent.mkdir(parents=True, exist_ok=True); c.save(p, quality=85)
        COLUMNISTS[i] = (name, series, author, f"/static/thumb/face-{key}.jpg")

def kw(a):
    t = re.sub(r"[\[\]\"'“”‘’…·,.!?()]", " ", a["title"])
    words = [w for w in t.split() if len(w) >= 2][:8]
    return ",".join([secname(a)] + words)

def build():
    if DIST.exists(): shutil.rmtree(DIST)
    shutil.copytree(ROOT / "static", DIST / "static")
    for f in ("robots.txt",) + (() if NO_CNAME else ("CNAME",)): shutil.copy(ROOT / f, DIST / f)
    shutil.copy(ROOT / "static/favicon.ico", DIST / "favicon.ico")
    arts = load()
    make_thumbs(arts)
    try: make_faces()
    except ImportError: pass
    news = [a for a in arts if not a["column"]]
    cols = [a for a in arts if a["column"]]
    # ── 메인 (모바일 순서대로 마크업, PC는 CSS grid 8:4로 재배치)
    head = next((a for a in news if a.get("thumb")), arts[0])
    subs = [a for a in news if a is not head and a.get("thumb")][:3]
    if len(subs) < 3: subs += [a for a in arts if a is not head and a not in subs][:3 - len(subs)]
    used = {id(head)} | {id(a) for a in subs}
    top = f"""<section class="h-top"><div class="lead"><a href="{head['url']}"><span class="lph"><img src="{head['photo']}" alt=""></span>
<span class="kick">■ {secname(head)}</span><strong>{esc(head['title'])}</strong><p>{esc(head.get('subtitle') or head['excerpt'])}</p>{meta_line(head)}</a></div>
<ul class="subs">{"".join(row(a, ex=False) for a in subs)}</ul></section>"""
    latest = f'<section class="h-latest">{boxh("최신기사", "/section/all/")}<ul class="tline">{"".join(timeline(a) for a in arts[:8])}</ul></section>'
    blocks = ""
    for k, v in SECTIONS.items():
        if k == "opinion": continue
        sa = [a for a in arts if a["section"] == k]
        if not sa: continue
        first = next((a for a in sa if a.get("thumb") and id(a) not in used), next((a for a in sa if id(a) not in used), sa[0]))
        others = [a for a in sa if a is not first][:3]
        blocks += f'<section class="sec">{boxh("■ " + v, f"/section/{k}/")}<ul class="first">{row(first)}</ul><ul class="tl">{"".join(tline(a) for a in others)}</ul></section>'
    photos = [a for a in news if a.get("thumb") and id(a) not in used][:4]
    strip = f'<section class="h-photo">{boxh("포토뉴스")}<div>' + "".join(f'<a href="{a["url"]}">{thumb(a)}<span>{esc(a["title"])}</span></a>' for a in photos) + "</div></section>"
    more = f'<section class="h-more">{boxh("뉴스 더보기", "/section/all/")}<ul class="rows">{"".join(row(a) for a in arts[8:14])}</ul></section>'
    body = f'<div class="home">{top}{latest}{colbox(arts)}<div class="h-secs">{blocks}</div><div class="h-side">{rank(arts, n=10, skip=16)}{ADSLOT}{columnists(arts)}</div>{strip}{more}</div>'
    write("/", page("", body, arts=arts, keywords="뉴스더힐,식품,유통,전통시장,소상공인,칼럼"))
    # ── 섹션 (+ 전체기사)
    for k, v in list(SECTIONS.items()) + [("all", "전체기사")]:
        sa = arts if k == "all" else [a for a in arts if a["section"] == k]
        lst = "".join(row(a) for a in sa) or f'<li class="empty"><b>준비 중입니다</b><span>{v} 기사를 준비하고 있습니다. 곧 찾아뵙겠습니다.</span></li>'
        body = f"""<div class="cols"><div class="mainc"><p class="crumb"><a href="/">홈</a> &gt; <b>{v}</b></p>
<h1 class="sech">{v}<small>총 {len(sa)}건</small></h1><ul class="rows list">{lst}</ul></div>{sidebar(arts)}</div>"""
        write(f"/section/{k}/", page(v, body, url=f"/section/{k}/", active=k, arts=arts, keywords=f"뉴스더힐,{v}"))
    for old, target in (("distribution", "food"), ("market", "food"), ("editorial", "opinion"), ("column", "opinion")):
        url = f"/section/{target}/"
        name = SECTIONS[target]
        write(f"/section/{old}/", f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={url}"><link rel="canonical" href="{SITE}{url}"><title>{name} - 뉴스더힐</title></head><body><a href="{url}">{name} 섹션으로 이동</a></body></html>')
    # ── 기사
    for a in arts:
        same = [x for x in arts if x["section"] == a["section"] and x is not a][:6]
        img = a.get("photo") or "/static/og-default.jpg"
        ld = json.dumps({"@context": "https://schema.org", "@type": "NewsArticle", "headline": a["title"], "datePublished": f"{a['dt']:%Y-%m-%d}" + (f"T{a['time']}:00+09:00" if a.get("time") else ""), "author": {"@type": "Person", "name": a["author"]}, "publisher": {"@type": "Organization", "name": NAME}}, ensure_ascii=False)
        byline_email = esc(a["reporter_email"]) if a.get("reporter_email") else f'<a href="mailto:{EMAIL}">{EMAIL}</a>'
        kicker = esc(a["kicker"])
        kicker_label = f'<p class="okick">{kicker}</p>' if kicker else ""
        body = f"""<div class="cols"><div class="mainc"><article class="post">
<p class="crumb"><a href="/">홈</a> &gt; <a href="/section/{a['section']}/">{secname(a)}</a></p>
<header class="ah">{kicker_label}<h1>{esc(a['title'])}</h1>{f'<p class="sub">{esc(a["subtitle"])}</p>' if a.get('subtitle') else ''}
<div class="info"><ul><li>기자명 <b>{esc(a['author'])}</b></li><li>입력 {dt(a)}</li>{('<li>수정 ' + esc(a['updated']) + '</li>') if a.get('updated') else ''}</ul>
<span class="fs"><button type="button" data-d="-" aria-label="글자 작게">가-</button><button type="button" data-d="+" aria-label="글자 크게">가+</button></span></div></header>
<div class="body">{a['html']}</div>
<p class="byl">{esc(a['author'])} {byline_email}</p>
<p class="cr">저작권자 © 뉴스더힐 무단전재 및 재배포 금지</p>
<p class="share"><a href="mailto:?subject={esc(a['title'])}&amp;body={SITE}{a['url']}">메일 공유</a></p>
</article>
<section class="rel">{boxh(secname(a) + " 다른 기사", f"/section/{a['section']}/")}<ul class="rows">{''.join(row(x, ex=False) for x in same)}</ul></section>
</div>{sidebar(arts, a)}</div>
<script type="application/ld+json">{ld}</script>"""
        write(a["url"], page(a["title"], body, desc=a["desc"], url=a["url"], image=img, active=a["section"], ogtype="article", arts=arts, keywords=kw(a)))
    # 고정 페이지
    for f in sorted((ROOT / "pages").glob("*.md")):
        raw = f.read_text(encoding="utf-8"); m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
        meta = dict(re.findall(r"^(\w+):\s*(.*)$", m.group(1), re.M))
        write(meta["url"], page(meta["title"], f'<div class="cols"><div class="mainc"><article class="post"><header class="ah"><h1>{esc(meta["title"])}</h1></header><div class="body">{md(m.group(2))}</div></article></div>{sidebar(arts)}</div>', url=meta["url"], arts=arts))
    # RSS
    items = "".join(f"<item><title>{esc(a['title'])}</title><link>{SITE}{a['url']}</link><guid>{SITE}{a['url']}</guid><pubDate>{format_datetime(a['dt'].replace(hour=9))}</pubDate><description>{esc(a['desc'])}</description></item>" for a in arts[:30])
    (DIST / "rss.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{NAME}</title><link>{SITE}/</link><description>{TAGLINE}</description><language>ko</language>{items}</channel></rss>', encoding="utf-8")
    # sitemap
    urls = ["/", "/about/"] + [f"/section/{k}/" for k in list(SECTIONS) + ["all"]] + [a["url"] for a in arts]
    (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{SITE}{u}</loc></url>" for u in urls) + "</urlset>", encoding="utf-8")
    print(f"built {len(arts)} articles → {DIST}")

if __name__ == "__main__": build()
