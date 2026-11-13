# 칼럼 게시 절차 (외부 칼럼니스트)

처음 작성 2026-10-22. 교수님 지시: "칼럼 올릴 때 사진 계속 올려줘". 칼럼을 올릴 때는 **항상 칼럼니스트 대표 이미지를 본문 맨 위에 넣는다.**

## 1. 원고 받기
- 원고는 kj@abanable.com 메일로 온다(Claude in Chrome '직장' 프로필, `/mail/u/0/`). 예: 박현 손해사정사 `lnclaim@naver.com`, 제목 `[박현 손해사정사의 정당한 보험금 리포트] …`.
- 메일 본문을 그대로 쓴다. 칼럼은 필자 의견이므로 문장을 고치지 않는다. 명백한 오타만 고치고, 고친 곳은 보고한다.
- 붙여 넣은 뒤 원문과 같은지 확인한다(공백 줄 정리 후 SHA-256 비교 등).
- 수치·판례·기관 발표는 검색으로 확인하고, 확인 못 한 것은 보고에 [미검증]으로 적는다(본문은 고치지 않고 교수님께 여쭙는다).

## 2. 대표 이미지 (필수)
- 출처: 구글드라이브 `뉴스더힐/칼럼리스트` 폴더(폴더 ID `14RB0DC9dVFSoqHATo9SxDx5saH9di2u3`, 교수님 PC의 `E:\내 드라이브\뉴스더힐\칼럼리스트`). Google_Drive 커넥터 `search_files`(`parentId = '…'`) → `download_file_content`로 받는다.

| 필자(author) | 파일 | slug 접두 |
|---|---|---|
| 박현 손해사정사 | 박현.png | hyun- |
| 단지팀장(백효연) | 단지.png | danji- |
| 최경집 | 최경집.png (= static/column-header-sisun.jpg) | kj- 등 |

- 가로 1000px JPEG(품질 85)로 줄여 `static/img/<slug>-photo1.jpg`로 저장하고, 본문 첫 줄에 `![제목에서 머리말을 뺀 부분](/static/img/<slug>-photo1.jpg)`. 캡션은 달지 않는다(기존 칼럼과 같음).
- 메일에 원고용 사진이 따로 오면 그 사진을 대표 이미지로 쓰고, 칼럼리스트 이미지는 쓰지 않는다.
- 폴더에 없는 새 필자면 게시 전에 교수님께 이미지를 요청한다.
- 최경집 교수 칼럼은 5절.

## 3. front matter
```
title: [연재명] 제목
section: opinion
kind: 칼럼
author: 박현 손해사정사
date: YYYY-MM-DD
slug: hyun-YYYYMMDD0000N
column: true
time: HH:MM
```

## 4. 검증·배포
docs/songpa-auto-publish.md 5~6절과 같다(build.py, 화면 확인, redesign 푸시, backup/main-<SHA>, main 배포, CNAME 유지).

## 5. 최경집 교수 칼럼
- 교수님 10/22 지시로 같은 폴더의 `최경집.png`(사이트의 `static/column-header-sisun.jpg`와 같은 그림)를 본문 맨 위에 넣는다: `![최경집 교수의 시선](/static/column-header-sisun.jpg)`.
- 10/22 기준 공개된 최경집 칼럼 18편 모두 이 그림이 들어가 있다(옛 기사는 `static/old/kj-…-0.png`, 빠져 있던 4편은 이날 추가).

## 6. 자동 게시에서 박현·단지팀장 칼럼 올리기 (2026-11-13 추가)
교수님 11/13 "박현 칼럼 안올라갔는데" → 자동 게시 작업에 넣기로 함("응"). 통합 자동 게시(docs/auto-publish-all.md 4-B)가 회차마다 처리한다.
- 같은 날 교수님 "단지팀장것도 있자나" → 단지팀장 칼럼도 같은 방법으로 자동 게시한다.
- 찾기: Gmail 커넥터 `search_threads` `(from:lnclaim@naver.com OR from:taki102@naver.com) -label:뉴스더힐-처리 newer_than:14d`.
  - 박현(lnclaim@naver.com): 제목 `[박현 손해사정사의 정당한 보험금 리포트] …` → author `박현 손해사정사`, slug `hyun-YYYYMMDD0000N`.
  - 단지팀장(백효연, taki102@naver.com): 제목에 `단지팀장의 보험 칼럼`이 들어간 원고(메일 제목의 `[`가 빠지거나 `]` 뒤 띄어쓰기가 없을 때가 있다 → title은 `[보험보상전문가 단지팀장의 보험 칼럼] 제목`으로 맞춘다) → author `단지팀장(백효연)`, slug `danji-YYYYMMDD0000N`. 메일 본문 첫 줄에 제목이 없을 수 있다.
  - 원고가 아닌 메일(문의·수정 요청 등)은 게시하지 않고 보고한다. 수정 요청이면 이미 올린 칼럼을 고칠지 교수님께 여쭙는다.
- 본문: `get_message`(기본 PLAIN_TEXT는 문장 사이 띄어쓰기가 빠지므로 `FULL_CONTENT`의 htmlBody로 문단·띄어쓰기를 확인). 원문 그대로 쓰고 문장을 고치지 않는다. 번호 목록의 굵은 소제목은 `## 1. …`로. 붙여 넣은 뒤 공백을 뺀 글자가 원문과 같은지 python으로 비교한다.
- 메일 첫 줄의 제목은 본문에서 빼고 title로 쓴다. 이미 `articles/`에 같은 제목이 있으면 쓰지 않고 라벨만 붙인다.
- 이미지: 메일에 원고용 사진 첨부가 있으면 `download_gmail_attachment`로 받아 1000px JPEG로 쓴다. 없으면 필자 대표 이미지(직전 같은 필자 칼럼의 `static/img/hyun-…-photo1.jpg` / `danji-…-photo1.jpg`와 같은 파일 = 드라이브 박현.png / 단지.png)를 새 slug 이름(`…-photo1.jpg`)으로 복사한다.
- front matter는 3절 그대로(author는 위 필자명, `section: opinion`, `kind: 칼럼`, `column: true`, slug 위 접두, time은 게시 시각). 출처 문장·편집국 명의 넣지 않는다.
- 수치·약관·법 조항은 확인하되 본문은 고치지 않는다. 틀려 보이는 곳은 게시하되 보고에 [확인 필요]로 적는다. 명예훼손·특정 보험사 실명 비방 등 판단이 서지 않으면 `draft: true`로 두고 보고.
- 처리 후 메일에 Label_14('뉴스더힐-처리').
