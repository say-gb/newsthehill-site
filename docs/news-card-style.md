# 뉴스더힐 카드 스타일 (Canva 대안 기본값)

처음 작성 2026-10-29. 교수님: 자체 그래픽 "안 이쁘다" → "예전에 코덱스로 해서 만들었는데"(2027 식품외식산업전망 카드뉴스 4장, news-2026102700005-cn1~4). 그 스타일을 기본으로 한다.
Canva 크레딧이 없거나 Canva를 못 쓸 때 `scripts/make_infographic.py` 대신 이것을 쓴다.

## 규칙
- 서체: 제목·큰 숫자는 Black Han Sans(`tools/cards/bhs.woff2`, OFL), 본문은 Noto Sans CJK KR, 출처·섹션은 Noto Serif CJK KR.
- 색: 딥그린 #12402F / 아이보리 #F5F1E6 / 골드 #B08A3E / 살몬 #E57755. 다른 색 쓰지 않는다.
- 배경은 딥그린(강한 경고·핵심 숫자 하나) 또는 아이보리(목록·일정). 같은 날 카드끼리 배경을 섞는다.
- 왼쪽 위 `NEWS THE HILL`, 오른쪽 위 골드 섹션명, 아래 `자료: ○○ · 뉴스더힐` + 발표일.
- 제목은 2줄, 짧게. 큰 숫자 1~3개만. 문장 설명은 넣지 않는다.
- 샘플: `tools/cards/sample-dark.html`(큰 숫자형), `sample-rows.html`(목록형), `sample-date.html`(일정형). 복사해서 글자만 바꾼다.
- 렌더: `python3 tools/cards/render.py tools/cards/<카드>.html static/img/news-…-card.jpg` → 렌더된 그림을 Read로 열어 겹침·잘림을 꼭 확인한다.
- 카드 숫자는 원문과 대조. 캡션 `*그래픽=뉴스더힐(자료: ○○)*`. 다 쓴 카드 HTML은 지운다(샘플만 남김).
