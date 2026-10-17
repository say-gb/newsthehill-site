/*! blankfill.js v0.1 (미리보기) — 뉴스더힐 빈 공간 배너 삽입
 * 특허 제10-2410472호(주식회사 더에이블) 청구항 10의 5단계를 정적 사이트에서 구현:
 *  1) 레이아웃 정보로 구성요소 위치·크기 측정   2) 웹페이지 스캔으로 블랭크 영역 탐색
 *  3) 기준보다 작은 블랭크가 여럿이면 인접 구성요소를 재배열해 하나로 병합(≥1024px)
 *  4) 블랭크 크기에 맞는 타겟 데이터(배너) 선택 — 키워드 점수 P = A·(1−x) + B·x
 *  5) 블랭크 위치에 배너를 삽입해 웹페이지와 함께 표시 (닫기 시 원상복구)
 * 서버·쿠키 없음. 개인 키워드(A)는 이 브라우저 localStorage의 최근 읽은 기사 키워드만 사용.
 */
(function () {
  "use strict";
  var me = document.currentScript || {};
  var CFG_URL = (me.dataset && me.dataset.banners) || "/static/banners/banners.json";
  var MIN_VIEW = 1024;              // 병합(재배열)은 1024px 이상에서
  var GAP = 12;                      // 배너 사이·가장자리 여백
  var DEBUG = /[?&]bf=debug/.test(location.search);
  var cfg = null, slots = [], timers = [], closed = sessionStorage.getItem("nth_bf_closed") === "1";
  var state = { rects: 0, blanks: [], merged: false, placed: [] };
  window.__blankfill = state;

  function log() { if (DEBUG && window.console) console.log.apply(console, ["[blankfill]"].concat([].slice.call(arguments))); }

  /* ---------- 1단계: 구성요소 위치·크기 ---------- */
  var SEL = "h1,h2,h3,h4,p,li,img,figure,time,input,button,table,dl,blockquote,.logo,.lab,.ticker,.photo a,.cbox a";
  function measure() {
    var out = [], sx = window.scrollX, sy = window.scrollY;
    document.querySelectorAll(SEL).forEach(function (el) {
      if (el.closest(".nth-blank-slot")) return;
      var cs = getComputedStyle(el);
      if (cs.visibility === "hidden" || cs.display === "none" || +cs.opacity === 0) return; // 무효 구성요소 제외
      var r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) return;
      out.push({ x: r.left + sx, y: r.top + sy, w: r.width, h: r.height });
    });
    state.rects = out.length;
    return out;
  }

  /* ---------- 2단계: 블록 묶기 + 블랭크 스캔 (x축 → y축) ---------- */
  function scan(rects) {
    var main = document.querySelector("main"), foot = document.querySelector("footer");
    if (!main) return [];
    var top = main.getBoundingClientRect().top + scrollY;
    var bottom = (foot ? foot.getBoundingClientRect().top : main.getBoundingClientRect().bottom) + scrollY;
    var W = document.documentElement.clientWidth;
    // 본문 세로 범위에 걸친 박스들의 x구간을 합쳐 블록 영역 생성
    var iv = rects.filter(function (r) { return r.y < bottom && r.y + r.h > top; })
      .map(function (r) { return [Math.max(0, r.x), Math.min(W, r.x + r.w)]; })
      .sort(function (a, b) { return a[0] - b[0]; });
    var blocks = [];
    iv.forEach(function (s) {
      var last = blocks[blocks.length - 1];
      if (last && s[0] <= last[1] + 8) last[1] = Math.max(last[1], s[1]); else blocks.push([s[0], s[1]]);
    });
    // 블록 사이(가로) 빈 구간 → 각 구간을 세로로 스캔해 블록 없는 직사각형
    var blanks = [], cur = 0;
    blocks.concat([[W, W]]).forEach(function (b) {
      if (b[0] - cur > 0) {
        var x0 = cur, x1 = b[0];
        var hit = rects.some(function (r) { return r.x < x1 && r.x + r.w > x0 && r.y < bottom && r.y + r.h > top; });
        if (!hit) blanks.push({ x: x0, y: top, w: x1 - x0, h: bottom - top, side: x0 < W / 2 ? "left" : "right" });
      }
      cur = Math.max(cur, b[1]);
    });
    // 본문 안의 예약 빈칸(빈 컨테이너, 구성요소 0개)도 블랭크로 취급
    document.querySelectorAll("[data-bf-slot]").forEach(function (el) {
      var r = el.getBoundingClientRect(), x = r.left + scrollX, y = r.top + scrollY;
      if (r.width < 2 || el.offsetParent === null) return;
      var hit = rects.some(function (q) { return q.x < x + r.width && q.x + q.w > x && q.y < y + r.height && q.y + q.h > y; });
      if (!hit) blanks.push({ x: x, y: y, w: r.width, h: r.height, side: "inline", el: el });
    });
    var min = cfg.min_blank || { w: 120, h: 200 };
    blanks.forEach(function (b) { b.small = b.w < min.w || b.h < min.h; });
    log("blanks", JSON.stringify(blanks));
    return blanks;
  }

  /* ---------- 3단계: 작은 블랭크 여러 개 → 구성요소 재배열로 병합 ---------- */
  function mergeIfNeeded(blanks) {
    var small = blanks.filter(function (b) { return b.small && b.side !== "inline" && b.w >= 8; });
    var root = document.documentElement;
    if (window.innerWidth < MIN_VIEW || small.length < 2) return false;
    var total = small.reduce(function (s, b) { return s + b.w; }, 0);
    // 본문 컨테이너(.wrap)를 왼쪽으로 붙여 좌·우 여백을 오른쪽 한 줄기로 모음 (특허 도 6)
    var LEFT = 8;
    root.style.setProperty("--bf-left", LEFT + "px");
    // 합친 줄기가 가장 좁은 배너보다 작으면 본문 폭을 줄여 블랭크를 확대 (종속항 9·18, 도 9)
    var minW = Math.min.apply(null, cfg.banners.map(function (b) { return b.w; })) + GAP * 2;
    var wrap = document.querySelector(".wrap"), ww = wrap ? wrap.getBoundingClientRect().width : 0;
    var vw = document.documentElement.clientWidth;
    if (vw - LEFT - ww < minW) {
      var nw = vw - LEFT - minW;
      if (nw < 800) return false;                         // 너무 줄어들면 하지 않음
      root.style.setProperty("--bf-wrap", nw + "px");
    }
    root.classList.add("bf-merged");
    state.merged = { from: small.length, total: Math.round(total) };
    log("merged", small.length, "blanks", total, "px →", vw - LEFT - (parseFloat(root.style.getPropertyValue("--bf-wrap")) || ww), "px");
    return true;
  }

  /* ---------- 4단계: 크기 맞는 배너 고르기 + 키워드 점수 ---------- */
  function pageKeywords() {
    var s = [];
    var mk = document.querySelector('meta[name="keywords"]');
    if (mk) s = s.concat(mk.content.split(","));
    document.querySelectorAll("h1, .post .lab, main h2").forEach(function (e, i) { if (i < 12) s.push(e.textContent); });
    return s.join(" ");
  }
  function personalKeywords() {
    try { return (JSON.parse(localStorage.getItem("nth_reads") || "[]")).join(" "); } catch (e) { return ""; }
  }
  function ratio(kws, text) {
    if (!kws.length || !text) return 0;
    var n = kws.filter(function (k) { return text.indexOf(k) >= 0; }).length;
    return n / kws.length;
  }
  function candidates(blank) {
    var today = new Date().toISOString().slice(0, 10), x = cfg.x == null ? 0.5 : cfg.x;
    var B = pageKeywords(), A = personalKeywords();
    return cfg.banners.filter(function (b) {
      var excluded = (b.exclude_paths || []).some(function (path) { return location.pathname.indexOf(path) === 0; });
      if (b.active === false || excluded || (b.advertiser === "낭만클럽" && location.pathname.indexOf("/articles/") === 0)) return false;
      return (!b.start || b.start <= today) && (!b.end || b.end >= today);
    }).map(function (b) {
      var scale = blank.el ? 1 : Math.min(1, (blank.w - GAP * 2) / b.w);        // 폭이 조금 모자라면 비율 축소
      var kws = b.advertiser === "낭만클럽" ? [] : (b.keywords || []);
      var p = ratio(kws, A) * (1 - x) + ratio(kws, B) * x;
      return { b: b, scale: scale, w: Math.round(b.w * scale), h: Math.round(b.h * scale), score: p + (b.priority || 0) * 0.01 };
    }).filter(function (c) { return c.scale >= 0.8 && c.h <= blank.h; })
      .sort(function (a, b) { return b.score - a.score; });
  }
  // 세로로 긴 블랭크는 배너 높이 단위로 분할해 여러 칸을 만든다 (종속항 8·17)
  function split(blank, cands) {
    var out = [], y = blank.el ? blank.y : blank.y + GAP, used = {};
    for (var i = 0; i < cands.length; i++) {
      var c = cands[i];
      if (used[c.b.id] || window.__bfUsed[c.b.id] || y + c.h > blank.y + blank.h) continue;
      if (blank.el && out.length) break;
      if (blank.el && (c.w !== blank.w || c.h !== blank.h)) continue;   // 예약칸은 크기 정확히 일치
      out.push({ x: blank.x + (blank.w - c.w) / 2, y: y, c: c, el: blank.el, rest: cands.filter(function (o) { return o !== c; }) });
      used[c.b.id] = 1; window.__bfUsed[c.b.id] = 1; y += c.h + GAP * 2;
    }
    return out;
  }

  /* ---------- 5단계: 삽입 ---------- */
  function render(slot) {
    var a = document.createElement("aside");
    if (slot.el) { a.className = "nth-blank-slot inline"; fill(a, slot.c); slot.el.appendChild(a); slot.el.classList.add("filled");
      state.placed.push({ id: slot.c.b.id, slot: "inline", w: slot.c.w, h: slot.c.h, score: +slot.c.score.toFixed(3) }); return a; }
    a.className = "nth-blank-slot";
    a.style.cssText = "position:absolute;left:" + Math.round(slot.x) + "px;top:" + Math.round(slot.y) + "px;width:" + slot.c.w + "px;z-index:3";
    fill(a, slot.c);
    document.body.appendChild(a);
    // 후보가 더 있으면 일정 시간마다 순차 표시(로테이션)
    var pool = [slot.c].concat(slot.rest.filter(function (o) { return o.w === slot.c.w && o.h === slot.c.h; })), k = 0;
    if (pool.length > 1) timers.push(setInterval(function () { k = (k + 1) % pool.length; fill(a, pool[k]); }, (cfg.rotate_sec || 30) * 1000));
    state.placed.push({ id: slot.c.b.id, x: Math.round(slot.x), y: Math.round(slot.y), w: slot.c.w, h: slot.c.h, score: +slot.c.score.toFixed(3) });
    return a;
  }
  function fill(a, c) {
    var b = c.b, sep = b.href.indexOf("?") < 0 ? "?" : "&";
    var href = /^#/.test(b.href) ? b.href : b.href + sep + "utm_source=newsthehill&utm_medium=blankfill&utm_content=" + encodeURIComponent(b.id);
    var noLabel = b.type === "ad" && b.img_label;
    a.setAttribute("aria-label", b.type === "ad" ? "광고" : "추천");
    a.innerHTML = '<div class="bf-lab' + (noLabel ? ' nolab' : '') + '">' + (noLabel ? "" : (b.type === "ad" ? "광고" : "추천")) +
      '<button type="button" aria-label="닫기">×</button></div><a href="' + href + '"><img src="' + b.img + '" width="' + c.w + '" height="' + c.h +
      '" alt="' + (b.type === "ad" ? "광고: " : "") + (b.advertiser || "") + " 배너" + '"></a>';
    a.querySelector("button").onclick = function () { sessionStorage.setItem("nth_bf_closed", "1"); closed = true; run(); };
  }

  function reset() {
    slots.forEach(function (s) { s.remove(); }); slots = [];
    timers.forEach(clearInterval); timers = [];
    document.documentElement.classList.remove("bf-merged");
    document.documentElement.style.removeProperty("--bf-wrap");
    document.querySelectorAll("[data-bf-slot]").forEach(function (e) { e.classList.remove("filled", "bf-empty"); });
    state.merged = false; state.placed = [];
  }

  function hideEmptySlots() {
    document.querySelectorAll("[data-bf-slot]").forEach(function (e) { e.classList.toggle("bf-empty", !e.classList.contains("filled")); });
  }

  function run() {
    reset();
    if (closed || !cfg) { hideEmptySlots(); return; }
    window.__bfUsed = {};
    var narrow = window.innerWidth < 1024;                    // 모바일: 여백 줄기 없음 → 본문 예약칸만
    var blanks = scan(measure());
    if (narrow) blanks = blanks.filter(function (b) { return b.el; });
    else if (mergeIfNeeded(blanks)) blanks = scan(measure()); // 재배열 후 다시 스캔
    state.blanks = blanks;
    blanks.filter(function (b) { return !b.small; }).sort(function (a, b) { return (b.el ? 1 : 0) - (a.el ? 1 : 0); }).forEach(function (b) {
      split(b, candidates(b)).forEach(function (s) { slots.push(render(s)); });
    });
    if (DEBUG) blanks.forEach(function (b) {
      var d = document.createElement("div"); d.className = "nth-blank-slot";
      d.style.cssText = "position:absolute;left:" + b.x + "px;top:" + b.y + "px;width:" + b.w + "px;height:" + b.h + "px;outline:2px dashed " + (b.small ? "#c00" : "#090") + ";pointer-events:none";
      document.body.appendChild(d); slots.push(d);
    });
    hideEmptySlots();
    log("placed", JSON.stringify(state.placed));
  }

  // 읽은 기사 키워드 기록(개인 키워드 A) — 이 브라우저에만 저장, 서버 전송 없음
  function remember() {
    var mk = document.querySelector('meta[name="keywords"]');
    if (!mk || !document.querySelector("article.post")) return;
    try {
      var arr = JSON.parse(localStorage.getItem("nth_reads") || "[]");
      arr = mk.content.split(",").map(function (s) { return s.trim(); }).filter(Boolean).concat(arr).slice(0, 20);
      localStorage.setItem("nth_reads", JSON.stringify(arr));
    } catch (e) {}
  }

  var t;
  function later() { clearTimeout(t); t = setTimeout(run, 300); }
  function start() {
    remember();
    fetch(CFG_URL).then(function (r) { return r.json(); }).then(function (j) {
      cfg = j; run();
      window.addEventListener("resize", later);
      window.addEventListener("load", later);
      document.querySelectorAll("main img").forEach(function (i) { if (!i.complete) i.addEventListener("load", later, { once: true }); });
    }).catch(function (e) { log("config error", e); run(); });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
