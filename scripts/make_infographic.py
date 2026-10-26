#!/usr/bin/env python3
"""뉴스더힐 인포그래픽 카드(기사 대표 이미지) 생성기 v2 — HTML/CSS를 Playwright로 그려 1200×675 JPEG로 저장.
사진을 쓸 수 없는 보도자료 기사용. 저작권은 뉴스더힐. (v1: scripts/make_info_card.py)

사용: python3 scripts/make_infographic.py spec.json static/img/news-XXXX-card.jpg

spec.json 필드(모두 선택, title만 필수):
  theme   "light"(아이보리, 기본) | "dark"(네이비)
  kicker  상단 분류 라벨. 예: "식품 회수"
  title   ["1줄", "2줄"]  (최대 2줄)
  lead    제목 아래 한 줄 설명
  alert   빨간 띠 문구(회수·위해 기사). 예: "섭취 중단 · 구입처 반품"
  hero    {"value": "54.2%", "unit": "↓", "label": "애호박 도매가, 평년 대비"}  큰 숫자 하나
  bars    [{"label": "애호박", "value": 54.2, "text": "54.2%↓", "note": "20개 9,716원"}, ...]  가로 막대(최대 5개, value 비율로 길이)
  tiles   [{"icon": "calendar", "label": "일시", "value": "11월 11일(수)", "note": "보조 설명"}, ...]  아이콘 칸(최대 4개)
  rows    v1 형식 [라벨, 값, 보조]도 받는다 → tiles로 바꿔 그림
  source  "자료: 식품의약품안전처"
아이콘: calendar clock won chart down up alert box pin users check info phone globe leaf truck gift flask school medal ship
"""
import json, sys, html, io
from pathlib import Path

W, H = 1200, 675

ICONS = {  # 24x24 stroke 아이콘(자체 제작 단순 도형)
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "won": '<path d="M4 6l3 12 5-10 5 10 3-12M3 11h18M3 14h18"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "down": '<path d="M12 4v15M6 13l6 6 6-6"/>',
    "up": '<path d="M12 20V5M6 11l6-6 6 6"/>',
    "alert": '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.5"/>',
    "box": '<path d="M3 7l9-4 9 4v10l-9 4-9-4z"/><path d="M3 7l9 4 9-4M12 11v10"/>',
    "pin": '<path d="M12 21s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12z"/><circle cx="12" cy="9" r="2.5"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2 20c0-4 3-6 7-6s7 2 7 6"/><circle cx="17" cy="9" r="2.5"/><path d="M17 14c3 0 5 2 5 5"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M7.5 12.5l3 3 6-6"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    "phone": '<path d="M5 3h4l2 5-3 2a12 12 0 006 6l2-3 5 2v4a2 2 0 01-2 2A17 17 0 013 5a2 2 0 012-2z"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>',
    "leaf": '<path d="M5 19C5 9 11 4 20 4c0 9-5 15-15 15z"/><path d="M5 19l8-8"/>',
    "truck": '<path d="M2 6h12v10H2zM14 10h4l3 3v3h-7"/><circle cx="6" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',
    "gift": '<rect x="3" y="9" width="18" height="12" rx="1"/><path d="M3 13h18M12 9v12M12 9c-2-4-6-4-6-1.5S10 9 12 9zM12 9c2-4 6-4 6-1.5S14 9 12 9z"/>',
    "flask": '<path d="M9 3h6M10 3v6L4 19a1.5 1.5 0 001.3 2h13.4a1.5 1.5 0 001.3-2L14 9V3"/><path d="M7 15h10"/>',
    "school": '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c0 2 3 3 6 3s6-1 6-3v-5"/>',
    "medal": '<circle cx="12" cy="15" r="6"/><path d="M8 3l4 6 4-6M12 12.5v5"/>',
    "ship": '<path d="M3 15l2 5h14l2-5zM5 15V9h14v6M9 9V5h6v4"/>',
}

THEMES = {
    "light": dict(bg="#F6F1E7", ink="#1F2638", sub="#5B6275", accent="#B8862F", card="#FFFFFF", line="#E4DCCB",
                  band="#283043", bandink="#F6F1E7", bar="#283043", bartrack="#E9E2D3", chip="#283043", chipink="#F3D58F"),
    "dark": dict(bg="#232A3B", ink="#FFFFFF", sub="#B9C0CF", accent="#E2B85C", card="rgba(255,255,255,0.07)", line="rgba(255,255,255,0.14)",
                 band="#171C29", bandink="#C9CFDB", bar="#E2B85C", bartrack="rgba(255,255,255,0.10)", chip="#E2B85C", chipink="#232A3B"),
}

def e(s): return html.escape(str(s))

def icon(name, color):
    p = ICONS.get(name, ICONS["info"])
    return f'<svg viewBox="0 0 24 24" width="30" height="30" fill="none" stroke="{color}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">{p}</svg>'

def build_html(s):
    t = THEMES.get(s.get("theme", "light"), THEMES["light"])
    tiles = s.get("tiles") or [{"label": r[0], "value": r[1], "note": r[2] if len(r) > 2 else "", "icon": "info"} for r in s.get("rows", [])]
    bars, hero = s.get("bars", [])[:5], s.get("hero")
    title = "<br>".join(e(x) for x in s["title"][:2])
    kicker = f'<span class="chip">{e(s.get("kicker", "식품·유통"))}</span>' if s.get("kicker", "x") else ""
    alert = f'<div class="alert">{icon("alert", "#fff")}<span>{e(s["alert"])}</span></div>' if s.get("alert") else ""
    lead = f'<p class="lead">{e(s["lead"])}</p>' if s.get("lead") else ""
    hero_html = ""
    if hero:
        hero_html = f'''<div class="hero"><div class="hv">{e(hero["value"])}<small>{e(hero.get("unit", ""))}</small></div>
          <div class="hl">{e(hero.get("label", ""))}</div></div>'''

    if bars:  # 왼쪽: 제목·히어로 / 오른쪽: 막대그래프
        mx = max(float(b["value"]) for b in bars) or 1
        rows = "".join(f'''<div class="br"><div class="bl">{e(b["label"])}</div>
            <div class="bt"><div class="bf" style="width:{max(8, 100*float(b["value"])/mx):.1f}%"></div></div>
            <div class="bv">{e(b.get("text", b["value"]))}<em>{e(b.get("note", ""))}</em></div></div>''' for b in bars)
        cap = f'<div class="bcap">{e(s.get("bars_caption", ""))}</div>' if s.get("bars_caption") else ""
        body = f'''<div class="split"><div class="left">{kicker}<h1>{title}</h1>{lead}{alert}{hero_html}</div>
          <div class="right card">{cap}{rows}</div></div>'''
    else:  # 위: 제목 / 아래: 아이콘 칸
        n = len(tiles[:4]) or 1
        cells = "".join(f'''<div class="tile card"><div class="ti">{icon(x.get("icon", "info"), t["accent"])}</div>
            <div class="tl">{e(x["label"])}</div><div class="tv">{e(x["value"])}</div>
            <div class="tn">{e(x.get("note", ""))}</div></div>''' for x in tiles[:4])
        top_right = hero_html if hero else ""
        body = f'''<div class="top"><div>{kicker}<h1>{title}</h1>{lead}</div>{top_right}</div>{alert}
          <div class="grid" style="grid-template-columns:repeat({n},minmax(0,1fr))">{cells}</div>'''

    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;background:{t["bg"]};color:{t["ink"]};font-family:"Noto Sans CJK KR","Noto Sans KR",sans-serif;position:relative;overflow:hidden}}
.wrap{{position:absolute;inset:0 0 58px 0;padding:46px 60px 30px}}
.deco{{position:absolute;right:-120px;top:-120px;width:380px;height:380px;border-radius:50%;border:44px solid {t["accent"]};opacity:.10}}
.chip{{display:inline-block;background:{t["chip"]};color:{t["chipink"]};font-weight:700;font-size:21px;letter-spacing:.5px;padding:7px 16px;border-radius:999px;margin-bottom:18px}}
h1{{white-space:nowrap;font-family:"Noto Serif CJK KR","Noto Serif KR",serif;font-weight:900;font-size:54px;line-height:1.22;letter-spacing:-1.5px}}
.lead{{margin-top:12px;font-size:23px;color:{t["sub"]};font-weight:500}}
.card{{background:{t["card"]};border:1px solid {t["line"]};border-radius:18px;box-shadow:0 6px 18px rgba(20,25,40,.06)}}
.split{{display:grid;grid-template-columns:470px 1fr;gap:40px;height:100%;align-items:center}}
.hero{{margin-top:22px}} .hv{{font-size:92px;font-weight:900;color:{t["accent"]};letter-spacing:-3px;line-height:1}}
.hv small{{font-size:56px;margin-left:4px}} .hl{{margin-top:8px;font-size:22px;color:{t["sub"]};font-weight:500}}
.right{{padding:26px 30px;display:flex;flex-direction:column;gap:20px;justify-content:center;height:100%}}
.bcap{{font-size:19px;color:{t["sub"]};font-weight:500;margin-bottom:-4px}}
.br{{display:grid;grid-template-columns:118px 1fr 168px;align-items:center;gap:14px}}
.bl{{font-size:24px;font-weight:700}} .bt{{height:26px;background:{t["bartrack"]};border-radius:13px;overflow:hidden}}
.bf{{height:100%;background:{t["bar"]};border-radius:13px}}
.bv{{font-size:27px;font-weight:900;color:{t["accent"]};line-height:1.05;text-align:right}} .bv em{{display:block;font-style:normal;font-size:16px;font-weight:500;color:{t["sub"]};margin-top:3px}}
.top{{display:flex;justify-content:space-between;align-items:flex-start;gap:30px}} .top .hero{{margin-top:6px;text-align:right}}
.grid{{position:absolute;left:60px;right:60px;bottom:28px;display:grid;gap:18px}}
.tile{{padding:20px 22px 18px;min-height:178px}} .ti{{margin-bottom:10px}}
.tl{{font-size:19px;color:{t["sub"]};font-weight:700}} .tv{{white-space:nowrap;margin-top:6px;font-size:31px;font-weight:900;letter-spacing:-.8px;line-height:1.15;color:{t["ink"]}}}
.tn{{margin-top:7px;font-size:17px;color:{t["sub"]};line-height:1.35}}
.alert{{margin-top:18px;display:inline-flex;align-items:center;gap:10px;background:#C0392B;color:#fff;font-weight:700;font-size:22px;padding:9px 18px 9px 14px;border-radius:10px}}
.alert svg{{width:24px;height:24px}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:58px;background:{t["band"]};color:{t["bandink"]};display:flex;align-items:center;justify-content:space-between;padding:0 60px;font-size:19px}}
.foot b{{font-family:"Noto Serif CJK KR",serif;font-weight:900;letter-spacing:2px;font-size:20px;color:{t["accent"] if s.get("theme")=="dark" else "#F3D58F"}}}
</style></head><body><div class="deco"></div><div class="wrap">{body}</div>
<div class="foot"><span>{e(s.get("source", ""))}  ·  그래픽=뉴스더힐</span><b>NEWS THE HILL</b></div></body></html>'''

def render(spec, out):
    from playwright.sync_api import sync_playwright
    from PIL import Image
    doc = build_html(spec)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        pg.set_content(doc); pg.wait_for_timeout(150)
        # 넘치는 글자는 한 줄에 들어갈 때까지 줄인다(제목·칸 값·막대 값)
        pg.evaluate("""() => { const fit = (el, min) => { let f = parseFloat(getComputedStyle(el).fontSize);
            const box = el.parentElement; const lim = el.tagName==='H1' ? box.clientWidth : el.parentElement.clientWidth - 44;
            while (el.scrollWidth > lim && f > min) { f -= 1; el.style.fontSize = f + 'px'; } };
          document.querySelectorAll('.tv').forEach(el => fit(el, 18));
          document.querySelectorAll('h1').forEach(el => fit(el, 34)); }""")
        png = pg.screenshot(type="png")
        b.close()
    im = Image.open(io.BytesIO(png)).convert("RGB").resize((W, H), Image.LANCZOS)
    im.save(out, quality=90)

if __name__ == "__main__":
    render(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
