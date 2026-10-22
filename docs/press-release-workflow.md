# 보도자료 → 기사 작업 절차

info@newsthehill.com으로 들어오는 보도자료(주로 송파구청)를 뉴스더힐 기사로 올리는 절차다. 처음 작성 2026-10-21, 교수님 지시.

## 1. 메일 확인
- info@newsthehill.com은 kj@abanable.com 사용자의 별칭이다. Gmail 커넥터(kj@abanable.com)에서 `to:info@newsthehill.com` 으로 찾는다.
- 처리한 메일 스레드에는 Gmail 라벨 `뉴스더힐-처리` 를 붙인다. 이 라벨이 붙은 스레드는 다시 처리하지 않는다.
- Gmail 커넥터로는 첨부파일을 내려받을 수 없다. 사진은 교수님이 채팅에 올려 주시거나 드라이브 `뉴스더힐\YYYYMMDD` 폴더에 넣어 주신다.

## 2. 기사 쓰기 규칙
- 보도자료에 있는 사실만 쓴다. 숫자·날짜·이름·직함·인용문은 원문 그대로. 보도자료에 없는 내용은 추가하지 않는다.
- 날짜에 요일이 붙어 있으면 달력으로 맞는지 확인한다.
- 둘째 문단 안에 출처를 밝힌다: "○○구는 ○일 보도자료에서 이같이 밝혔다."
- 인용문은 "…"며 "…"고 말했다 형태로 다듬되 단어는 바꾸지 않는다.
- 제목은 핵심 사실(무엇을·언제)을 담아 한 줄, 부제는 대상·방식 요약.
- 본문 첫 줄은 `입력 YYYY-MM-DD`.
- 사진 캡션 끝에 `사진=○○구 제공`. 사진 속 인물 이름은 보도자료에 설명이 있을 때만 쓴다.
- 기자명: 최경집 (교수님 10/21 지시).
- 섹션: 지역 행정·행사 소식은 `local`(사회·문화).

## 3. 파일
- `articles/YYYY-MM-DD-news-YYYYMMDDNNNNN.md`, slug `news-YYYYMMDD0000N` (그날 이미 있는 번호 다음).
- front matter: title, subtitle, section, author, date, slug, time(게시 시각 HH:MM, KST), 초안이면 `draft: true`.
- 사진: `static/img/<slug>-photo1.jpg` (가로 1200px, JPEG 품질 82). 본문에 `![설명](/static/img/...)` 다음 줄에 빈 줄, 그다음 `*캡션*`.

## 4. 초안 → 게시
- 자동 실행(예약 작업)은 `draft: true` 로 redesign 브랜치에 커밋만 하고 게시하지 않는다. 교수님께 초안 요약을 보고한다.
- 교수님이 OK 하시면 `draft: true` 를 지우고 time을 게시 시각으로 바꾼 뒤 아래 배포 절차를 따른다.

## 5. 배포 (main = 빌드 결과)
1. redesign 브랜치에서 `OUT_DIR=<빈 폴더> python3 build.py`
2. main 체크아웃에서 `.git` 과 `CNAME` 을 뺀 모든 파일을 지우고 빌드 결과를 복사한다(CNAME은 원본 유지).
3. 커밋 메시지: `배포: redesign <짧은 SHA> 빌드 결과 — <내용>. CNAME 원본 유지. 이전 main <짧은 SHA>`
4. redesign, main 순서로 push. 2~3분 뒤 실제 페이지에서 확인한다.
