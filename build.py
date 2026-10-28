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
    "food": "식품·유통", "local": "사회·문화", "interview": "인터뷰",
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
        plain = html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"<figure>.*?</figure>", "", meta["html"], flags=re.S)))  # 사진 캡션은 요약에서 뺀다
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

LOGO = """<a class="logo" href="/" aria-label="뉴스더힐 홈"><!-- 원본 로고: 교수님 제공(2026-10-17 12:52 KST 채팅 첨부), 10/28 벡터화본 static/logo/newsthehill-logo.svg(원본에서 윤곽 추출, 어떤 크기에도 선명), 큰 PNG newsthehill-logo-4000.png / 이전 크롭본 newsthehill-logo.jpg / 원본 newsthehill-logo-original.jpg --><img src="/static/logo/newsthehill-logo.svg" alt="NEWS THE HILL 뉴스더힐" width="4381" height="974"></a>"""

def load_ticker_blocklist():
    try:
        lines = (ROOT / "config" / "ticker_blocklist.txt").read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return ["낭만클럽", "낭만호랑", "더에이블", "광고"]
    return [line for raw in lines if (line := raw.strip()) and not line.startswith("#")]

def load_ticker_exclude():
    try:
        lines = (ROOT / "config" / "ticker_exclude.txt").read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return set()
    return {line.strip("/").removeprefix("articles/")
            for raw in lines if (line := raw.strip()) and not line.startswith("#")}

def ticker_pick(arts):
    """티커는 머리기사 영역(머리기사+아래 3편)과 최신기사 목록에 없는 편집국·기자 기사 중 config/ticker_exclude.txt의 슬러그를 제외해 최대 6편, 없으면 숨김."""
    blocklist = load_ticker_blocklist()
    exclude = load_ticker_exclude()
    used = ticker_excluded_urls(arts)
    eligible = [a for a in arts
                if not any(word in a["title"] for word in blocklist)
                and a["slug"] not in exclude
                and a["column"] is False and a["section"] != "opinion"
                and a["url"] not in used]
    return sorted(eligible, key=lambda a: (a["dt"], a.get("time", ""), a["slug"]), reverse=True)[:6]

# Retain the collection itself as well as its result, so object IDs cannot be reused.
_ticker_cache = None

def cached_ticker_pick(arts):
    global _ticker_cache
    if _ticker_cache is None or _ticker_cache[0] is not arts:
        _ticker_cache = (arts, ticker_pick(arts))
    return _ticker_cache[1]

def header(active, arts):
    menu = "".join(f'<a href="/section/{k}/"{" class=on" if k == active else ""}>{v}</a>' for k, v in SECTIONS.items())
    ticker_arts = cached_ticker_pick(arts)
    tick = "".join(
        f'<li{' aria-hidden="true"' if i else ""}><a href="{esc(a["url"])}"{' tabindex="-1" aria-hidden="true"' if i else ""}>'
        f'<span class="tk-t">{a["dt"]:%m.%d}{esc(" " + a["time"]) if a.get("time") else ""}</span> {esc(a["title"])}</a></li>'
        for i, a in enumerate(ticker_arts)
    )
    ticker = f'''<div class="ticker" role="region" aria-label="뉴스"><div class="wrap"><b>뉴스</b><div class="tk-window"><ul id="tick" aria-live="off">{tick}</ul></div><button class="tk-toggle" type="button" aria-label="뉴스 자동 넘김 일시정지/재생" aria-pressed="false" title="자동 넘김 일시정지/재생"><span aria-hidden="true">❚❚</span></button></div></div>''' if ticker_arts else ""
    return f"""<header class="hd">
<div class="mast"><div class="wrap">
<p class="date"><span id="today">{today()}</span><span id="wx" class="wx"></span></p>
{LOGO}
<div class="tools"><form class="srch" action="https://www.google.com/search" role="search"><input type="hidden" name="as_sitesearch" value="newsthehill.com"><input name="q" placeholder="기사 검색" aria-label="검색어"><button aria-label="검색"><svg viewBox="0 0 20 20" width="16" height="16"><circle cx="8.5" cy="8.5" r="6" fill="none" stroke="currentColor" stroke-width="2"/><path d="M13 13l5 5" stroke="currentColor" stroke-width="2"/></svg></button></form>
<button class="ham" type="button" aria-label="전체메뉴"><svg viewBox="0 0 20 20" width="20" height="20"><path d="M2 5h16M2 10h16M2 15h16" stroke="currentColor" stroke-width="2"/></svg></button></div>
</div></div>
<nav class="gnb" aria-label="주메뉴"><div class="wrap">{menu}</div></nav>
{ticker}
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
(function(){
var W=['일','월','화','수','목','금','토'],n=new Date(),t=document.getElementById('today');if(t)t.textContent=n.getFullYear()+'년 '+(n.getMonth()+1)+'월 '+n.getDate()+'일('+W[n.getDay()]+')';
var C={0:'맑음',1:'대체로 맑음',2:'구름 조금',3:'흐림',45:'안개',48:'안개',51:'이슬비',53:'이슬비',55:'이슬비',61:'비',63:'비',65:'강한 비',71:'눈',73:'눈',75:'많은 눈',80:'소나기',81:'소나기',82:'강한 소나기',95:'뇌우'};
fetch('https://api.open-meteo.com/v1/forecast?latitude=37.48&longitude=127.14&current=temperature_2m,weather_code&timezone=Asia%2FSeoul').then(function(r){return r.json()}).then(function(j){var c=j.current;document.getElementById('wx').textContent='송파 '+(C[c.weather_code]||'')+' '+Math.round(c.temperature_2m)+'℃'}).catch(function(){});
document.querySelectorAll('.fs button').forEach(function(b){b.onclick=function(){var x=document.querySelector('.body');var s=parseFloat(getComputedStyle(x).fontSize)+(b.dataset.d==='+'?1:-1);x.style.fontSize=Math.max(14,Math.min(24,s))+'px'}});
var f=document.querySelector('.srch');if(f)f.addEventListener('submit',function(e){var i=f.querySelector('input[name=q]');if(getComputedStyle(i).display==='none'||!i.value){e.preventDefault();f.classList.add('open');i.focus()}});
var h=document.querySelector('.ham');if(h)h.onclick=function(){document.documentElement.classList.toggle('menu-open')};})();
</script><script src="/static/js/blankfill.js" data-banners="/static/banners/banners.json" defer></script><script src="/static/js/ticker.js" defer></script>"""

import hashlib as _h
CSSV = _h.md5((ROOT / "static/style.css").read_bytes()).hexdigest()[:8]  # 스타일 바꾸면 브라우저가 새로 받게

# 검색엔진 소유 확인 태그 (구글 서치콘솔 kj@abanable.com 계정, 2026-10-27). 네이버 서치어드바이저(https://newsthehill.com) 2026-10-27 추가.
SITE_VERIFY = {
    "google-site-verification": "X54i-CIF1cEqhm-KWgoIELRfcwUH5u2ttQG_TsMs68Y",
    "naver-site-verification": "81d5f1c4ebf7bc5215d2900d19f9b066cbd5dc90",
}
VERIFY = "".join(f'<meta name="{k}" content="{v}">' for k, v in SITE_VERIFY.items() if v)


def page(title, body, desc=TAGLINE, url="/", image="/static/og-default.jpg", active="", ogtype="website", arts=(), keywords=""):
    full = f"{title} - {NAME}" if title else f"{NAME} - {TAGLINE}"
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">{VERIFY}
<title>{esc(full)}</title><meta name="description" content="{esc(desc)}">{f'<meta name="keywords" content="{esc(keywords)}">' if keywords else ''}
<link rel="canonical" href="{SITE}{url}"><link rel="icon" href="/favicon.ico" sizes="32x32"><link rel="icon" type="image/png" href="/static/favicon.png"><link rel="apple-touch-icon" href="/static/favicon.png">
<meta property="og:site_name" content="{NAME}"><meta property="og:type" content="{ogtype}"><meta property="og:title" content="{esc(title or NAME)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{SITE}{url}"><meta property="og:image" content="{SITE}{image}"><meta property="og:locale" content="ko_KR">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#283043">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;700;900&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" rel="stylesheet">
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="/rss.xml"><link rel="stylesheet" href="/static/style.css?v={CSSV}"><link rel="stylesheet" href="/static/css/motion.css">
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

def rank_pick(arts, cur=None, n=10, skip=None):
    """주요 뉴스: 칼럼·오피니언은 빼고 기사만. front matter 'pick: true'(편집국 선정)를 먼저, 나머지는 최신순으로 채운다.
    skip은 예전 호출과의 호환용으로 남겨 두고 쓰지 않는다(2026-10-20 교수님 지시)."""
    news = [a for a in arts if a is not cur and not a["column"] and a["section"] != "opinion"]
    picked = [a for a in news if a.get("pick", "").lower() == "true"]
    return (picked + [a for a in news if a not in picked])[:n]

def rank(arts, cur=None, n=10, skip=8, *, picked=None):
    top = rank_pick(arts, cur, n, skip) if picked is None else picked
    return f'<section class="rankbox">{boxh("주요 뉴스")}<ol class="rank">' + "".join(f'<li><b>{i+1}</b><a href="{a["url"]}">{esc(a["title"])}</a></li>' for i, a in enumerate(top)) + "</ol></section>"

def columnists_pick(arts):
    return [last for _, _, author, _ in COLUMNISTS
            if (last := next((a for a in arts if a["author"] == author and a["column"]), None)) is not None]

def columnists(arts, *, picked=None):
    last_by_author = {a["author"]: a for a in (columnists_pick(arts) if picked is None else picked)}
    cb = ""
    for name, series, author, ph in COLUMNISTS:
        last = last_by_author.get(author)
        if not last: continue
        cb += f'<li><a href="{last["url"]}"><span class="cph"><img src="{ph}" alt="{esc(name)}" loading="lazy"></span><b>{esc(series)}</b><span class="ct">{esc(clean(last["title"]))}</span></a></li>'
    return f'<section class="cbox">{boxh("칼럼니스트", "/section/opinion/")}<ul>{cb}</ul></section>'

def sidebar(arts, cur=None):
    return f'<aside class="side">{rank(arts, cur)}{ADSLOT}{columnists(arts)}</aside>'

COLBOX_BYLINE = {"최경집": "최경집 식품마케팅 교수"}
COLBOX_THEME = {"최경집": "c-kj", "박현 손해사정사": "c-hyun", "단지팀장(백효연)": "c-danji"}  # 10/28 교수님: 필자마다 박스 배경색 다르게  # 박스 아래 필자 표기(없으면 저자 문자열 그대로)

def colbox_pick(arts):
    # 10/28 교수님: "칼럼도 3명이 최신일 때마다 바꿔줘" — 칼럼니스트 3명 중 가장 최근에 쓴 사람이 박스 주인공,
    # 오른쪽 목록은 나머지 칼럼니스트들의 최근 칼럼(사람마다 1편씩 먼저, 모자라면 최근순)
    authors = {author for _, _, author, _ in COLUMNISTS}
    cols = [a for a in arts if a["column"] and a["author"] in authors]
    c = cols[0] if cols else None
    if not c: return None, []
    rest = [a for a in cols if a is not c]
    others = []
    for _, _, author, _ in COLUMNISTS:
        if author == c["author"]: continue
        x = next((a for a in rest if a["author"] == author), None)
        if x: others.append(x)
    others += [a for a in rest if a not in others]
    others.sort(key=lambda a: (a["dt"], a.get("time", "")), reverse=True)
    return c, others[:3]

def colbox(arts, *, picked=None):  # 칼럼니스트 아이보리 박스(최신 칼럼니스트가 주인공)
    c, others = colbox_pick(arts) if picked is None else picked
    if not c: return ""
    name, series, author, ph = next(x for x in COLUMNISTS if x[2] == c["author"])
    first = re.sub(r"<[^>]+>", "", c["html"]).strip().split("\n")[0][:120]
    byline = COLBOX_BYLINE.get(author, author)
    def who(a):
        return {"단지팀장(백효연)": "단지팀장", "박현 손해사정사": "박현"}.get(a["author"], a["author"])
    return f"""<section class="sisun {COLBOX_THEME.get(author, '')}"><a class="sface" href="{c['url']}"><img src="{ph}" alt="{esc(name)}"></a>
<div class="stx"><p class="slab">{esc(series)}</p><a href="{c['url']}"><strong>{esc(clean(c['title']))}</strong><p>{esc(first)}…</p></a><em class="m">{esc(byline)}<i>|</i>{dt(c)}</em></div>
<ul class="smore">{''.join(f'<li><a href="{a["url"]}"><b class="sw">{esc(who(a))}</b> {esc(clean(a["title"]))}</a><time>{a["dt"]:%m.%d}</time></li>' for a in others)}</ul></section>"""

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
            im = Image.open(p).convert("RGB")
            if im.height > im.width * 0.8:  # 세로 사진(인물 등)은 목록 칸(3:2)에서 머리가 잘리지 않게 위쪽 기준으로 자른다
                h = round(im.width * 2 / 3); top = min(round(im.height * 0.04), im.height - h)
                if a.get("thumb_focus"):  # 카드뉴스처럼 제목이 아래에 있으면 front matter thumb_focus(0~1, 세로 위치)로 자르는 중심을 정한다
                    top = max(0, min(round(im.height * float(a["thumb_focus"]) - h / 2), im.height - h))
                im = im.crop((0, top, im.width, top + h))
            im.thumbnail((480, 480)); im.save(out, quality=80)
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

def _flag(a, key):
    return str(a.get(key, "")).lower() not in ("", "false", "0")

def _fresh(a, days=2):
    # 헤드라인 지정은 기사 날짜로부터 이틀까지만 유효 — 자동 게시가 이어져도 첫 화면이 굳지 않게
    from zoneinfo import ZoneInfo
    return (datetime.now(ZoneInfo("Asia/Seoul")).date() - a["dt"].date()).days <= days

def _songpa(a):
    return a["section"] == "local" and "송파" in (a["title"] + a.get("subtitle", ""))

def home_selection(arts):
    # 첫 화면 편집 규칙(교수님 10/28 "공신력 있는 송파 관장·병원장, 송파 소식이 먼저, 나는 아직 유명하지 않다"):
    # 헤드라인 = 제일 최신 사진 기사(home: false·칼럼 제외)
    # 아래 3칸 = sub: 1·2·3(숫자 순, 기한 없음, 직접 내릴 때까지) → 송파구 소식 → 최신 사진 기사
    # home: false = 헤드라인·아래 3칸·포토뉴스에서 뺌(교수님 본인 인터뷰·기고 등). 최신기사·섹션 목록에는 그대로.
    news = [a for a in arts if not a["column"] and not str(a.get("home", "")).lower() == "false"]
    pics = [a for a in news if a.get("thumb")]
    head = pics[0] if pics else arts[0]  # 헤드라인 = 제일 최신 기사(교수님 10/28 15:15 지시)
    flagged = sorted([a for a in pics if a is not head and _flag(a, "sub")],
                     key=lambda a: int(a["sub"]) if str(a["sub"]).isdigit() else 9)
    songpa = [a for a in pics if a is not head and a not in flagged and _songpa(a) and _fresh(a, 3)]
    subs = (flagged + songpa + [a for a in pics if a is not head and a not in flagged and a not in songpa])[:3]
    if len(subs) < 3: subs += [a for a in news if a is not head and a not in subs][:3 - len(subs)]
    used = {id(head)} | {id(a) for a in subs}
    # 더바이어식 첫 화면(10/28): 헤드라인 옆 관련 기사 4줄, 3단(뉴스 목록 / 식품·유통 박스 / 사이드)
    rel = [a for a in news if id(a) not in used][:4]
    used_top = used | {id(a) for a in rel}
    hlist = [a for a in news if id(a) not in used_top][:6]
    food = [a for a in arts if a["section"] == "food"]
    box_first = next((a for a in food if a.get("thumb") and id(a) not in used_top), food[0] if food else None)
    box_others = [a for a in food if a is not box_first][:6]
    blocks = []
    for k, v in SECTIONS.items():
        if k in ("opinion", "food"): continue  # 식품·유통은 가운데 박스로(10/28)
        sa = [a for a in arts if a["section"] == k]
        if not sa:
            if k == "interview": blocks.append((k, v, None, []))
            continue
        first = next((a for a in sa if a.get("thumb") and id(a) not in used), next((a for a in sa if id(a) not in used), sa[0]))
        others = [a for a in sa if a is not first][:3]
        blocks.append((k, v, first, others))
    colbox_main, colbox_others = colbox_pick(arts)
    return dict(head=head, subs=subs, latest=arts[:8], rel=rel, hlist=hlist, box_first=box_first, box_others=box_others,
                colbox_main=colbox_main, colbox_others=colbox_others, blocks=blocks,
                rank_top=rank_pick(arts, n=10, skip=16), columnists_last=columnists_pick(arts),
                photos=[a for a in news if a.get("thumb") and id(a) not in used][:4], more=arts[8:14])

def ticker_excluded_urls(arts):
    selected = home_selection(arts)
    articles = [selected["head"], *selected["subs"], *selected["latest"]]
    return {a["url"] for a in articles if a is not None}

def build():
    if DIST.exists(): shutil.rmtree(DIST)
    shutil.copytree(ROOT / "static", DIST / "static")
    for f in ("robots.txt",) + (() if NO_CNAME else ("CNAME",)): shutil.copy(ROOT / f, DIST / f)
    shutil.copy(ROOT / "static/favicon.ico", DIST / "favicon.ico")
    arts = load()
    make_thumbs(arts)
    try: make_faces()
    except ImportError: pass
    # ── 메인 (모바일 순서대로 마크업, PC는 CSS grid 8:4로 재배치)
    selected = home_selection(arts)
    head, subs = selected["head"], selected["subs"]
    rel_html = "".join(f'<li><a href="{a["url"]}">{esc(a["title"])}</a></li>' for a in selected["rel"])
    top = f"""<section class="h-top"><div class="lead2">
<a class="lt" href="{head['url']}"><span class="kick">■ {secname(head)}</span><strong>{esc(head['title'])}</strong></a>
<div class="lb"><a class="lph2" href="{head['url']}"><img src="{head['photo']}" alt=""></a>
<div class="lr"><a class="lsub" href="{head['url']}">{esc(head.get('subtitle') or head['excerpt'])}</a>{meta_line(head)}<ul class="rel">{rel_html}</ul></div></div></div>
<ul class="subs">{"".join(row(a, ex=False) for a in subs)}</ul></section>"""
    latest = f'<section class="h-latest">{boxh("최신기사", "/section/all/")}<ul class="tline">{"".join(timeline(a) for a in selected["latest"])}</ul></section>'
    blocks = ""
    for k, v, first, others in selected["blocks"]:
        lead = row(first) if first else f'<li class="empty"><span>{v} 기사를 준비하고 있습니다.</span></li>'
        blocks += f'<section class="sec">{boxh("■ " + v, f"/section/{k}/")}<ul class="first">{lead}</ul><ul class="tl">{"".join(tline(a) for a in others)}</ul></section>'
    hlist = f'<section class="h-list">{boxh("뉴스", "/section/all/")}<ul class="hl">{"".join(row(a) for a in selected["hlist"])}</ul></section>'
    bf, bo = selected["box_first"], selected["box_others"]
    box = ""
    if bf:
        box = (f'<section class="h-box">{boxh("식품·유통", "/section/food/")}'
               f'<a class="bxf" href="{bf["url"]}">{thumb(bf)}<strong>{esc(bf["title"])}</strong></a><ul class="bxl">'
               + "".join(f'<li><a href="{a["url"]}">{thumb(a)}<span>{esc(a["title"])}</span></a></li>' for a in bo) + '</ul></section>')
    photos = selected["photos"]
    strip = f'<section class="h-photo">{boxh("포토뉴스")}<div>' + "".join(f'<a href="{a["url"]}">{thumb(a)}<span>{esc(a["title"])}</span></a>' for a in photos) + "</div></section>"
    more = f'<section class="h-more">{boxh("뉴스 더보기", "/section/all/")}<ul class="rows">{"".join(row(a) for a in selected["more"])}</ul></section>'
    body = f'<div class="home home2">{top}{latest}{colbox(arts, picked=(selected["colbox_main"], selected["colbox_others"]))}{hlist}{box}<div class="h-secs">{blocks}</div><div class="h-side">{rank(arts, picked=selected["rank_top"])}{ADSLOT}{columnists(arts, picked=selected["columnists_last"])}</div>{strip}</div>'
    write("/", page("", body, arts=arts, keywords="뉴스더힐,식품,유통,전통시장,소상공인,칼럼"))
    # ── 섹션 (+ 전체기사)
    for k, v in list(SECTIONS.items()) + [("all", "전체기사")]:
        sa = arts if k == "all" else [a for a in arts if a["section"] == k]
        lst = "".join(row(a) for a in sa) or f'<li class="empty"><b>준비 중입니다</b><span>{v} 기사를 준비하고 있습니다. 곧 찾아뵙겠습니다.</span></li>'
        body = f"""<div class="cols"><div class="mainc"><p class="crumb"><a href="/">홈</a> &gt; <b>{v}</b></p>
<h1 class="sech">{v}<small>총 {len(sa)}건</small></h1><ul class="rows list">{lst}</ul></div>{sidebar(arts)}</div>"""
        write(f"/section/{k}/", page(v, body, url=f"/section/{k}/", active=k, arts=arts, keywords=f"뉴스더힐,{v}"))
    for old, target in (("distribution", "food"), ("market", "food"), ("editorial", "opinion"), ("column", "opinion"), ("people", "interview")):
        url = f"/section/{target}/"
        name = SECTIONS[target]
        write(f"/section/{old}/", f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={url}"><link rel="canonical" href="{SITE}{url}"><title>{name} - 뉴스더힐</title><script>location.replace("{url}" + location.search + location.hash)</script></head><body><a href="{url}">{name} 섹션으로 이동</a></body></html>')
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
<div class="info"><ul><li><b>{esc(a['author'])}</b></li><li>입력 {dt(a)}</li>{('<li>수정 ' + esc(a['updated']) + '</li>') if a.get('updated') else ''}</ul>
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
