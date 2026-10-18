# 글꼴(자체 호스팅)
2026-10-18 뉴스더힐봇. 카카오톡 인앱 브라우저 '보안인증서 문제 콘텐츠 차단' 대비로 외부 글꼴 연결(cdn.jsdelivr.net·fonts.googleapis.com·fonts.gstatic.com)을 없앰.

- pretendard/: Pretendard v1.3.9 dynamic subset woff2, 굵기 400·500·600·700 (각 92조각). 출처 cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/packages/pretendard/dist/web/static/woff2-dynamic-subset/. 라이선스 SIL OFL 1.1 — pretendard/LICENSE.txt
- noto-serif-kr/: Noto Serif KR Google Fonts v32 woff2 unicode-range 조각 124개(가변 글꼴, 700·900 두 굵기로 선언 — 구글 원본 CSS와 같은 방식). 라이선스 SIL OFL 1.1 — noto-serif-kr/OFL.txt (github.com/google/fonts/ofl/notoserifkr)
- fonts.css: 위 두 글꼴 @font-face. 브라우저는 페이지에 나온 글자가 든 조각만 받음(unicode-range).
- 쓰는 굵기는 headless Chrome 측정(document.fonts loaded)으로 정함: Pretendard 400/500/600/700, Noto Serif KR 700/900. 옛 링크의 Noto 600은 실제로 쓰이지 않음.
