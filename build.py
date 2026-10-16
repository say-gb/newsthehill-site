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
    "food": "식품", "distribution": "유통", "market": "소상공인·시장",
    "people": "사람들", "column": "칼럼",
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
        if l.startswith(">"): flush(); out.append("<blockquote>" + inline(l.lstrip("> ")) + "</blockquote>"); continue
        if lst: flush()
        para.append(l)
    flush()
    return "\n".join(out)

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
        plain = re.sub(r"<[^>]+>", "", meta["html"])
        meta["desc"] = meta.get("subtitle") or plain[:110]
        meta["excerpt"] = plain[:90].strip() + "…"
        meta["url"] = f"/articles/{meta['slug']}/"
        meta["column"] = meta.get("column", "").lower() == "true" or meta["section"] == "column"
        arts.append(meta)
    arts.sort(key=lambda a: (a["dt"], a["slug"]), reverse=True)
    return arts

LOGO = """<a class="logo" href="/" aria-label="뉴스더힐 홈">
<span class="wm">NEWS <small>THE</small> HILL</span>
<svg viewBox="0 0 300 18" preserveAspectRatio="none" aria-hidden="true"><path d="M0 17 C40 15 60 9 95 8 C120 7 130 2 150 2 C175 2 190 8 215 9 C250 10 270 15 300 17 Z" fill="currentColor"/></svg>
</a>"""

SEAL = """<svg class="seal" viewBox="0 0 120 120" aria-label="NEWS THE HILL PRESS"><defs><path id="ta" d="M20 60 A40 40 0 0 1 100 60"/><path id="tb" d="M18 62 A42 42 0 0 0 102 62"/></defs>
<circle cx="60" cy="60" r="57" fill="#1B2556" stroke="#C9A24B" stroke-width="3"/><circle cx="60" cy="60" r="50" fill="none" stroke="#C9A24B" stroke-width="1"/>
<text font-family="Georgia,serif" font-size="13" fill="#C9A24B" letter-spacing="1"><textPath href="#ta" startOffset="50%" text-anchor="middle">NEWS THE HILL</textPath></text>
<text font-family="Georgia,serif" font-size="13" fill="#C9A24B" letter-spacing="3"><textPath href="#tb" startOffset="50%" text-anchor="middle" side="right">PRESS</textPath></text>
<path d="M28 68 C42 66 48 58 60 57 C72 58 78 66 92 68 Z" fill="#C9A24B"/></svg>"""

# 법정 표시사항(신문법). 휴대전화 번호는 게시하지 않음.
FOOTER = f"""<footer class="foot">
<div class="wrap">
{SEAL}
<p class="fname">제호 <b>뉴스더힐</b> · 인터넷신문 등록번호 <b>서울 아 56252</b> · 등록일 2025.11.24</p>
<p>발행인·편집인 최만수 · <b>청소년보호책임자 최만수</b></p>
<p>Tel 02-6951-5540 · Fax 070-4009-3314 · <a href="mailto:info@newsthehill.com">info@newsthehill.com</a></p>
<p>발행소 서울 송파구 위례광장로 199 성희트리차 501-30호</p>
<p>사무실 경기도 성남시 수정구 위례대로 83 밀리토피아호텔 B1, 21호</p>
<!-- TODO(교수님 확인): 최초 발행일(발행연월일) 표기 추가. -->
<p class="links"><a href="/about/">회사소개</a> · <a href="/policy/terms/">이용약관</a> · <a href="/policy/privacy/">개인정보처리방침</a> · <a href="/policy/youth/">청소년보호정책</a> · <a href="/rss.xml">RSS</a></p>
<p class="copy">© {datetime.now().year} 뉴스더힐. 무단 전재·재배포 금지.</p>
</div></footer>"""

def tabs(active=""):
    return '<nav class="tabs" aria-label="섹션">' + "".join(
        f'<a href="/section/{k}/"{" class=on" if k == active else ""}>{v}</a>' for k, v in SECTIONS.items()) + "</nav>"

def page(title, body, desc=TAGLINE, url="/", image="/static/og-default.jpg", active="", ogtype="website"):
    full = f"{title} | {NAME}" if title else f"{NAME} — {TAGLINE}"
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}{url}"><link rel="icon" href="/favicon.ico" sizes="32x32"><link rel="icon" type="image/png" href="/static/favicon.png"><link rel="apple-touch-icon" href="/static/favicon.png">
<meta property="og:site_name" content="{NAME}"><meta property="og:type" content="{ogtype}"><meta property="og:title" content="{esc(title or NAME)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{SITE}{url}"><meta property="og:image" content="{SITE}{image}"><meta property="og:locale" content="ko_KR">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#1B2556">
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="/rss.xml"><link rel="stylesheet" href="/static/style.css">
</head><body>
<header class="top"><div class="wrap">{LOGO}<p class="tag">{TAGLINE}</p></div>{tabs(active)}</header>
<main class="wrap">{body}</main>
{FOOTER}
</body></html>"""

def card(a, big=False):
    lab = '<span class="lab col">최경집 교수의 시선</span>' if a["column"] else f'<span class="lab">{SECTIONS[a["section"]]}</span>'
    return f"""<article class="card{' big' if big else ''}"><a href="{a['url']}">{lab}<h{2 if big else 3}>{esc(a['title'])}</h{2 if big else 3}>
<p>{esc(a['excerpt'] if big else a.get('subtitle',''))}</p><time datetime="{a['dt']:%Y-%m-%d}">{a['dt']:%Y.%m.%d}</time> · {esc(a['author'])}</a></article>"""

def write(path, s):
    p = DIST / path.lstrip("/"); p = p / "index.html" if not p.suffix else p
    if BASE != "/":  # 내부 링크·자산에 BASE 접두어 (canonical/OG는 절대주소라 영향 없음)
        s = re.sub(r'((?:href|src)=")/(?!/)', lambda m: m.group(1) + BASE, s)
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s, encoding="utf-8")

def build():
    if DIST.exists(): shutil.rmtree(DIST)
    shutil.copytree(ROOT / "static", DIST / "static")
    for f in ("robots.txt",) + (() if NO_CNAME else ("CNAME",)): shutil.copy(ROOT / f, DIST / f)
    shutil.copy(ROOT / "static/favicon.ico", DIST / "favicon.ico")
    arts = load()
    # 메인
    cols = [a for a in arts if a["column"]]
    body = ""
    if arts: body += card(arts[0], big=True)
    body += '<h2 class="sh">최신 기사</h2><div class="grid">' + "".join(card(a) for a in arts[1:7]) + "</div>"
    if cols:
        c = cols[0]
        body += f'<a class="colband" href="{c["url"]}"><img src="{COLUMN_HEADER}" alt="최경집 교수의 시선" loading="lazy" width="1000" height="800"><span><b>최경집 교수의 시선</b>{esc(c["title"].replace("[최경집 교수의 시선] ",""))}<small>매주 월요일</small></span></a>'
    for k, v in SECTIONS.items():
        sa = [a for a in arts if a["section"] == k][:3]
        if sa: body += f'<h2 class="sh"><a href="/section/{k}/">{v} ›</a></h2><div class="grid">' + "".join(card(a) for a in sa) + "</div>"
    write("/", page("", body))
    # 섹션
    for k, v in SECTIONS.items():
        sa = [a for a in arts if a["section"] == k]
        head = f'<img class="colhead" src="{COLUMN_HEADER}" alt="최경집 교수의 시선"><p class="intro">식품마케팅을 가르치는 최경집 교수가 매주 월요일 시장과 식탁 사이를 씁니다.</p>' if k == "column" else ""
        lst = "".join(card(a) for a in sa) or '<p class="empty">곧 첫 기사가 실립니다.</p>'
        write(f"/section/{k}/", page(v, f'<h1 class="sh">{v}</h1>{head}<div class="grid">{lst}</div>', url=f"/section/{k}/", active=k))
    # 기사
    for a in arts:
        same = [x for x in arts if x["section"] == a["section"]]
        i = same.index(a)
        nav = ""
        if i + 1 < len(same): nav += f'<a href="{same[i+1]["url"]}">‹ 이전 글</a>'
        if i > 0: nav += f'<a href="{same[i-1]["url"]}">다음 글 ›</a>'
        rel = [x for x in arts if x is not a][:3]
        top = f'<img class="colhead" src="{COLUMN_HEADER}" alt="최경집 교수의 시선" width="1000" height="800">' if a["column"] else ""
        img = COLUMN_HEADER if a["column"] else "/static/og-default.jpg"
        ld = json.dumps({"@context": "https://schema.org", "@type": "NewsArticle", "headline": a["title"], "datePublished": f"{a['dt']:%Y-%m-%d}", "author": {"@type": "Person", "name": a["author"]}, "publisher": {"@type": "Organization", "name": NAME}}, ensure_ascii=False)
        body = f"""<article class="post">{top}<a class="lab" href="/section/{a['section']}/">{SECTIONS[a['section']]}</a>
<h1>{esc(a['title'])}</h1>{f'<p class="sub">{esc(a["subtitle"])}</p>' if a.get('subtitle') else ''}
<p class="meta">{esc(a['author'])} · 입력 <time datetime="{a['dt']:%Y-%m-%d}">{a['dt']:%Y.%m.%d}</time>{(' · 수정 ' + esc(a['updated'])) if a.get('updated') else ''}</p>
<div class="body">{a['html']}</div>
<p class="share"><a href="mailto:?subject={esc(a['title'])}&amp;body={SITE}{a['url']}">메일로 공유</a></p>
<nav class="pn">{nav}</nav></article>
<h2 class="sh">관련 기사</h2><div class="grid">{''.join(card(x) for x in rel)}</div>
<script type="application/ld+json">{ld}</script>"""
        write(a["url"], page(a["title"], body, desc=a["desc"], url=a["url"], image=img, active=a["section"], ogtype="article"))
    # 고정 페이지
    for f in sorted((ROOT / "pages").glob("*.md")):
        raw = f.read_text(encoding="utf-8"); m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
        meta = dict(re.findall(r"^(\w+):\s*(.*)$", m.group(1), re.M))
        write(meta["url"], page(meta["title"], f'<article class="post"><h1>{esc(meta["title"])}</h1><div class="body">{md(m.group(2))}</div></article>', url=meta["url"]))
    # RSS
    items = "".join(f"<item><title>{esc(a['title'])}</title><link>{SITE}{a['url']}</link><guid>{SITE}{a['url']}</guid><pubDate>{format_datetime(a['dt'].replace(hour=9))}</pubDate><description>{esc(a['desc'])}</description></item>" for a in arts[:30])
    (DIST / "rss.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{NAME}</title><link>{SITE}/</link><description>{TAGLINE}</description><language>ko</language>{items}</channel></rss>', encoding="utf-8")
    # sitemap
    urls = ["/", "/about/"] + [f"/section/{k}/" for k in SECTIONS] + [a["url"] for a in arts]
    (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{SITE}{u}</loc></url>" for u in urls) + "</urlset>", encoding="utf-8")
    print(f"built {len(arts)} articles → {DIST}")

if __name__ == "__main__": build()
