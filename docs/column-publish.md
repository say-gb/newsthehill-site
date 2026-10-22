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
